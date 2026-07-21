from fastapi import FastAPI
from app.routers import embed, query

app = FastAPI(title="fahemak-rag")

app.include_router(embed.router, tags=["embed"])
app.include_router(query.router, tags=["query"])

@app.get("/health")
async def health():
    return {"status": "ok"}