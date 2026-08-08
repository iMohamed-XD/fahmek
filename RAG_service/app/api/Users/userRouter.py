from typing import Annotated

from app.api.Users.dependencies import currentUserDep, serviceDep
from app.core.auth import create_access_token, create_refresh_token, decode_token
from app.schemas import RefreshRequest, Token, UserCreate, UserRead
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

UserRouter = APIRouter(prefix="/users", tags=["Users"])


@UserRouter.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserRead)
async def register(data: UserCreate, service: serviceDep) -> UserRead:
    user = await service.create_user(data)
    return UserRead.model_validate(user)


@UserRouter.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: serviceDep,
) -> Token:
    user = await service.authenticate(form_data.username, form_data.password)
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@UserRouter.post("/refresh", response_model=Token)
async def refresh(body: RefreshRequest, service: serviceDep) -> Token:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise unauthorized

    if payload.get("type") != "refresh":
        raise unauthorized

    user = await service.get_user(int(payload["sub"]))
    if user is None or user.token_version != payload.get("ver"):
        raise unauthorized

    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@UserRouter.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: currentUserDep, service: serviceDep) -> None:
    await service.bump_token_version(current_user)


@UserRouter.get("/me", response_model=UserRead)
async def get_me(current_user: currentUserDep) -> UserRead:
    return UserRead.model_validate(current_user)