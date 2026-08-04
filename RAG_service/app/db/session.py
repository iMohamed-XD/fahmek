
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

engine = create_engine(
    url="sqlite:///sqlite.db",
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