from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.db.models import Document
from app.db.session import sessionDep
from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate

router = APIRouter()

@router.get('/health', status_code=status.HTTP_200_OK)
def health():
    return {"status": "ok"}

@router.get("/documents/{id}", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def get_documents(session: sessionDep, id: int) -> DocumentRead | None:
    document: Document | None = await session.get(Document, id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Said id = {id} is not found in our Database",
        )
    return DocumentRead.model_validate(document)


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def add_document(data: DocumentCreate, session: sessionDep) -> dict[str, Any]:
    new_document = Document(**data.model_dump())
    session.add(new_document)
    await session.commit()
    await session.refresh(new_document)
    id = new_document.id
    return {
        "details": f"Given document ({new_document.name}) has been created successfully!!",
        "id": id,
    }


@router.put("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def edit_document(
    id: int, data: DocumentUpdate, session: sessionDep
) -> DocumentRead | None:
    new_document = await session.get(Document, id)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    new_document.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}))
    session.add(new_document)
    await session.commit()
    await session.refresh(new_document)
    return DocumentRead.model_validate(new_document)


@router.patch("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def patch_document(
    id: int, data: DocumentUpdate, session: sessionDep
) -> DocumentRead | None:
    new_document = await session.get(Document, id)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    new_document.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"}))
    session.add(new_document)
    await session.commit()
    await session.refresh(new_document)
    return DocumentRead.model_validate(new_document)


@router.delete("/documents/{id}", status_code=status.HTTP_200_OK)
async def delete_document(id: int, session: sessionDep) -> dict[str, str]:
    document = await session.get(Document, id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Given id = {id} is not found")
    name = document.name
    await session.delete(document)
    await session.commit()
    return {"details": f"the Document : {name} has been deleted successfully!!"}

