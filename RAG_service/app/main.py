from contextlib import asynccontextmanager

from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference

from app.api.router import router
from app.config import settings
from app.db.session import create_db

# db: DataBase



@asynccontextmanager
async def lifespan(app: FastAPI):
    # global db
    # db = DataBase()
    # db.init_db()
    await create_db()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.include_router(router)


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
@app.get('/health')
def health():
    return {"status": "ok"}

@app.get("/scalar", include_in_schema=False)
async def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title="Scalar API",
    )
