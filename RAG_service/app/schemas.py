from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr

from app.db.models import DocumentStatus


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str  # plaintext in, hashed before it ever reaches the model


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class DocumentCreate(BaseModel):
    name: str
    # path/status/user_id are server-assigned, never client-supplied — kept off this schema


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    status: DocumentStatus
    user_id: int

class DocumentUpdate(BaseModel):
    name: str | None = None
    status: DocumentStatus | None = None

class MsgCreate(BaseModel):
    content: str


class MsgRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    chat_id: int
    sender: str
    content: str
    date: date