from typing import Annotated

from app.core.auth import decode_token
from app.db.models import User
from app.db.session import get_session
from app.services.user import UserService
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

sessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_user_service(session: sessionDep) -> UserService:
    return UserService(session)


serviceDep = Annotated[UserService, Depends(get_user_service)]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    service: serviceDep,
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
    except ValueError:
        raise credentials_exception

    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = await service.get_user(int(user_id))
    if user is None:
        raise credentials_exception
    return user


currentUserDep = Annotated[User, Depends(get_current_user)]