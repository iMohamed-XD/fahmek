
from collections.abc import Generator
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

DB_PATH = Path(__file__).resolve().parent.parent.parent / "sqlite.db"

engine = create_engine(
    url=f"sqlite:///{DB_PATH}",
    echo=True,
    connect_args={
        "check_same_thread": False,
    }
)
def create_db():
    SQLModel.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    with Session(bind=engine) as session:
        yield session

sessionDep = Annotated[Session, Depends(get_session)]