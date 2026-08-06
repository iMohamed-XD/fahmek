from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document
from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, data: DocumentCreate) -> Document:
        new_document = Document(**data.model_dump())
        self.session.add(new_document)
        await self.session.commit()
        await self.session.refresh(new_document)
        return new_document

    async def get_document(self, id: int) -> Document:
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