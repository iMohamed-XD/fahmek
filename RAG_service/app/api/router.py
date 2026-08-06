from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.db.session import sessionDep
from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from app.services.document import DocumentService

router = APIRouter()

@router.get("/documents/{id}", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def get_documents(session: sessionDep, id: int) -> DocumentRead | None:
    service = DocumentService(session)
    document = await service.get_document(id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Said id = {id} is not found in our Database",
        )
    return DocumentRead.model_validate(document)


@router.post("/documents", status_code=status.HTTP_201_CREATED)
async def add_document(data: DocumentCreate, session: sessionDep) -> dict[str, Any]:
    service = DocumentService(session)
    new_document = await service.create_document(data)
    return {
        "details": f"Given document ({new_document.name}) has been created successfully!!",
        "id": new_document.id,
    }


@router.put("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def edit_document(
    id: int, data: DocumentUpdate, session: sessionDep
) -> DocumentRead | None:
    service = DocumentService(session)
    new_document = await service.update_document(id, data)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    return DocumentRead.model_validate(new_document)


@router.patch("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def patch_document(
    id: int, data: DocumentUpdate, session: sessionDep
) -> DocumentRead | None:
    service = DocumentService(session)
    new_document = await service.update_document(id, data)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    return DocumentRead.model_validate(new_document)


@router.delete("/documents/{id}", status_code=status.HTTP_200_OK)
async def delete_document(id: int, session: sessionDep) -> dict[str, Any]:
    service = DocumentService(session)
    result = await service.delete_document(id)
    if "was not found." in result["details"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["details"])
    return result