from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
# from app.routers import embed, query

app = FastAPI(title="fahemak-rag")

# app.include_router(embed.router, tags=["embed"])
# app.include_router(query.router, tags=["query"])

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/scalar", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(
        openapi_url = app.openapi_url,
        title = "Scalar API",
    )
