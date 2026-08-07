from datetime import date, datetime
from enum import Enum

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, Float, ForeignKey, Integer, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    chunking = "chunking"
    embedding = "embedding"
    indexed = "indexed"
    failed = "failed"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True, index=True)
    password_hash: Mapped[str]

    documents: Mapped[list["Document"]] = relationship(back_populates="user")
    chats: Mapped[list["Chat"]] = relationship(back_populates="user")


class Document(Base):
    __tablename__ = "document"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    path: Mapped[str]
    status: Mapped[DocumentStatus] = mapped_column(default=DocumentStatus.uploaded)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chats: Mapped[list["Chat"]] = relationship(secondary="chat_document", back_populates="documents")


class DocumentChunk(Base):
    __tablename__ = "document_chunk"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("document.id"))
    chunk_index: Mapped[int]
    content: Mapped[str]
    embedding: Mapped[list[float]] = mapped_column(Vector(384))
    token_count: Mapped[int]
    metadata_: Mapped[dict] = mapped_column("metadata", JSON)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))

    user: Mapped["User"] = relationship(back_populates="chats")
    msgs: Mapped[list["Msg"]] = relationship(back_populates="chat", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(secondary="chat_document", back_populates="chats")


# chat_document — pure association, no extra columns beyond the FKs -> plain Core Table
chat_document = Table(
    "chat_document",
    Base.metadata,
    Column("chat_id", ForeignKey("chat.id"), primary_key=True),
    Column("document_id", ForeignKey("document.id"), primary_key=True),
)


class Msg(Base):
    __tablename__ = "msg"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id"))
    sender: Mapped[str]  # 'user' | 'assistant'
    content: Mapped[str]
    date: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    chat: Mapped["Chat"] = relationship(back_populates="msgs")
    
    # Relationship to the association table
    msg_chunks: Mapped[list["MsgChunk"]] = relationship(back_populates="msg", cascade="all, delete-orphan")


class MsgChunk(Base):
    __tablename__ = "msg_chunk"

    msg_id: Mapped[int] = mapped_column(ForeignKey("msg.id"), primary_key=True)
    chunk_id: Mapped[int] = mapped_column(ForeignKey("document_chunk.id"), primary_key=True)
    similarity_score: Mapped[float]

    # Relationships back to parents
    msg: Mapped["Msg"] = relationship(back_populates="msg_chunks")
    chunk: Mapped["DocumentChunk"] = relationship()