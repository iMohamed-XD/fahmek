from typing import Any

from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from fastapi import APIRouter, HTTPException, status

from RAG_service.app.api.Documents.dependencies import serviceDep

DocumentRouter = APIRouter(prefix="/documents", tags=["Documents"])

@DocumentRouter.get("/documents/{id}/{field}", status_code=status.HTTP_200_OK)
async def get_document_field(id: int, field: str, service: serviceDep) -> dict[str, Any]:
    value = await service.get_document_field(id, field)
    return {field: value}


@DocumentRouter.get("/{id}", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def get_documents(service: serviceDep, id: int | None = None) -> DocumentRead | None:
    document = await service.get_document(id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Said id = {id} is not found in our Database",
        )
    return DocumentRead.model_validate(document)


@DocumentRouter.post("/", status_code=status.HTTP_201_CREATED)
async def add_document(data: DocumentCreate, service: serviceDep) -> dict[str, Any]:
    new_document = await service.create_document(data)
    return {
        "details": f"Given document ({new_document.name}) has been created successfully!!",
        "id": new_document.id,
    }


@DocumentRouter.put("/", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def edit_document(
    id: int, data: DocumentUpdate, service: serviceDep
) -> DocumentRead | None:
    new_document = await service.update_document(id, data)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    return DocumentRead.model_validate(new_document)


@DocumentRouter.patch("/", status_code=status.HTTP_200_OK, response_model=DocumentRead)
async def patch_document(
    id: int, data: DocumentUpdate, service: serviceDep
) -> DocumentRead | None:
    new_document = await service.update_document(id, data)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    return DocumentRead.model_validate(new_document)


@DocumentRouter.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_document(id: int, service: serviceDep) -> dict[str, Any]:
    result = await service.delete_document(id)
    if "was not found." in result["details"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=result["details"])
    return result
