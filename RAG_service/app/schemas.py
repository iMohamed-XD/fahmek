from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import DocumentType


class DocumentBase(BaseModel):
    name: str = Field(
        max_length=100,
        description="Name of said document, e.g. hello"
    )
    size: int = Field(
        le=150,
        ge=1,
        description="size in bytes of said document, e.g. 78"
    )
    uploaded_at: datetime 
    type: DocumentType = Field(
        description="type of said document, e.g. pdf"
    )

    model_config = ConfigDict(from_attributes=True)



class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int


class DocumentUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        max_length=100
    )
    size: int | None = Field(
        default=None,
        ge=1,
        le=150
    )
    uploaded_at: str | None = Field(
        default=None,
        min_length=8,
        max_length=50
    )
    type: DocumentType | None = None
