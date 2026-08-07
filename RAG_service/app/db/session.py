from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import settings
from app.db.models import Base

engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True,
)

async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session() as s:
        yield s

sessionDep = Annotated[AsyncSession, Depends(get_session)]