
from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class DocumentType(str, Enum):
    pdf = "pdf"
    txt = "txt"
    docx = "docx"
    doc = "doc"
    md = "md"

class Document(SQLModel, table=True):
    __tablename__ = "documents"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="Name of said document, e.g. hello")
    size: int = Field(ge=1, le=150, description="size in bytes of said document, e.g. 78")
    uploaded_at: datetime 
    type: DocumentType = Field(description="type of said document, e.g. pdf")