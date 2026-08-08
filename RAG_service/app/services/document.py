from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_document_field(self, id: int, field: str) -> Any:
        allowed_fields = set(DocumentRead.model_fields.keys())
        if field not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Field '{field}' does not exist on Document",
            )

        document = await self.session.get(Document, id)
        if document is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document with id {id} was not found.",
            )

        return getattr(document, field)

    async def create_document(self, data: DocumentCreate, *, user_id: int, path: str) -> Document:
        new_document = Document(**data.model_dump(), user_id=user_id, path=path)
        self.session.add(new_document)
        await self.session.commit()
        await self.session.refresh(new_document)
        return new_document

    async def get_document(self, id: int) -> Document | None:
        # Logic to retrieve a document from the database
        return await self.session.get(Document, id)

    async def update_document(self, id: int, data: DocumentUpdate) -> DocumentRead | None:
        new_document = await self.session.get(Document, id)
        if new_document is None:
            return None
        new_document.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}))
        self.session.add(new_document)
        await self.session.commit()
        await self.session.refresh(new_document)
        return new_document

    async def delete_document(self, id: int) -> dict[str, Any]:
        document = await self.session.get(Document, id)
        if document is None:
            return {
                "details": f"Document with id {id} was not found.",
                "id": id,
            }
        name = document.name
        await self.session.delete(document)
        await self.session.commit()
        return {
            "details": f"Given document ({name}) has been deleted successfully!!",
            "id": id,
        }