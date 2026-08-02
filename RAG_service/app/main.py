from fastapi import FastAPI, status, HTTPException
from contextlib import asynccontextmanager
from scalar_fastapi import get_scalar_api_reference
from app.schemas import DocumentCreate, DocumentUpdate, DocumentRead
from app.db.database import read_document, delete_document_sql, update_document, insert_document, read_documents, init_db
from typing import Any

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="fahemak-rag", lifespan=lifespan)

def check_field(field: str):
    allowed_fields = set(DocumentRead.model_fields.keys())

    if field not in allowed_fields:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field does not exist"
        )


def check_id_in_DB(id: int):
    if read_document(id=id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )


@app.get("/documnets/{id}/{field}", status_code=status.HTTP_200_OK)
def get_document_field(field: str, id: int) -> dict[str, Any]:
    check_field(field=field)
    check_id_in_DB(id=id)
    document: DocumentRead | None = read_document(id=id)
    return {
        field: getattr(document, field)
    }


@app.get("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def get_documents(id: int | None = None):
    document: DocumentRead | None = read_document(id=id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= f"Said id = {id} is not found in our Database"
        )
    return document


@app.post("/documents", status_code=status.HTTP_201_CREATED)
def add_document(data: DocumentCreate) -> dict[str, str]:
    insert_document(**data.model_dump())
    return {
        "details": f"Given document ({data.name}) has been created successfully!!",
    }


@app.put("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def edit_document(id: int, data: DocumentRead) -> DocumentRead | None:
    check_id_in_DB(id=id)
    update_document(
        id=id,
        **data.model_dump(exclude={"id"})
    )
    document: DocumentRead | None = read_document(id=id)
    return document


@app.patch("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def patch_document(id: int, data: DocumentUpdate) -> DocumentRead | None:
    check_id_in_DB(id)
    update_document(
        id=id,
        **data.model_dump(exclude_unset=True)
    )
    document: DocumentRead | None = read_document(id=id)
    return document


@app.delete("/documents", status_code=status.HTTP_200_OK)
def delete_document(id: int) -> dict[str, str]:
    check_id_in_DB(id=id)
    document: DocumentRead | None = read_document(id=id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail=f"Given id = {id} is not found"
        )
    name = document.name
    delete_document_sql(id=id)
    return {
        "details": f"the Document : {name} has been deleted successfully!!"
    }


@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
