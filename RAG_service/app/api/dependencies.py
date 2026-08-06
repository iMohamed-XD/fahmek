

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from RAG_service.app.services.document import DocumentService

sessionDep = Annotated[AsyncSession, Depends(get_session)]

def get_document_session(session: sessionDep) -> AsyncSession:
    return session

serviceDep = Annotated[DocumentService, Depends(get_document_session)]