from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from scalar_fastapi import get_scalar_api_reference

# from app.db.database import DataBase
from app.db.models import Document
from app.db.session import create_db, sessionDep
from app.schemas import DocumentCreate, DocumentRead, DocumentUpdate

# db: DataBase


@asynccontextmanager
async def lifespan(app: FastAPI):
    # global db
    # db = DataBase()
    # db.init_db()
    create_db()
    yield


app = FastAPI(title="fahemak-rag", lifespan=lifespan)


# def check_field(field: str):
#     allowed_fields = set(DocumentRead.model_fields.keys())

#     if field not in allowed_fields:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Field does not exist"
#         )


# def check_id_in_DB(id: int):
#     if db.read_document(id=id) is None:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Given id = {id} is not found in our DataBase!!!",
#         )


# @app.get("/documents/{id}/{field}", status_code=status.HTTP_200_OK)
# def get_document_field(field: str, id: int) -> dict[str, Any]:
#     check_field(field=field)
#     check_id_in_DB(id=id)
#     document: DocumentRead | None = db.read_document(id=id)
#     return {field: getattr(document, field)}


@app.get("/documents/{id}", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def get_documents(session: sessionDep, id: int) -> DocumentRead | None:
    document: Document | None = session.get(Document, id)
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Said id = {id} is not found in our Database",
        )
    return DocumentRead.model_validate(document)


@app.post("/documents", status_code=status.HTTP_201_CREATED)
def add_document(data: DocumentCreate, session: sessionDep) -> dict[str, Any]:
    new_document = Document(**data.model_dump())
    session.add(new_document)
    session.commit()
    session.refresh(new_document)
    id = new_document.id
    return {
        "details": f"Given document ({new_document.name}) has been created successfully!!",
        "id": id,
    }


@app.put("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def edit_document(
    id: int, data: DocumentRead, session: sessionDep
) -> DocumentRead | None:
    new_document = session.get(Document, id)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    new_document.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    session.add(new_document)
    session.commit()
    session.refresh(new_document)
    return DocumentRead.model_validate(new_document)


@app.patch("/documents", status_code=status.HTTP_200_OK, response_model=DocumentRead)
def patch_document(
    id: int, data: DocumentUpdate, session: sessionDep
) -> DocumentRead | None:
    new_document = session.get(Document, id)
    if new_document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Given id = {id} is not found in our DataBase!!!",
        )
    session.add(new_document)
    session.commit()
    session.refresh(new_document)
    new_document.sqlmodel_update(data.model_dump(exclude_unset=True, exclude_none=True))
    return DocumentRead.model_validate(new_document)


@app.delete("/documents/{id}", status_code=status.HTTP_200_OK)
def delete_document(id: int, session: sessionDep) -> dict[str, str]:
    document = session.get(Document, id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Given id = {id} is not found")
    name = document.name
    session.delete(document)
    session.commit()
    return {"details": f"the Document : {name} has been deleted successfully!!"}


@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
