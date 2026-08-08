from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import hash_password, verify_password
from app.db.models import User
from app.schemas import UserCreate, UserUpdate

# Fixed dummy hash so a login attempt against a nonexistent email still
# pays the bcrypt cost — closes the user-enumeration timing side channel.
_DUMMY_HASH = hash_password("not-a-real-password")


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, id: int) -> User | None:
        return await self.session.get(User, id)

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create_user(self, data: UserCreate) -> User:
        if await self.get_user_by_email(data.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with email '{data.email}' already exists.",
            )
        new_user = User(
            name=data.name,
            email=data.email.lower(),
            password_hash=hash_password(data.password),
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.get_user_by_email(email)
        hash_to_check = user.password_hash if user else _DUMMY_HASH
        password_ok = verify_password(password, hash_to_check)

        if user is None or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def bump_token_version(self, user: User) -> None:
        """Invalidates every outstanding refresh token for this user
        (logout-everywhere / password-change hook)."""
        user.token_version += 1
        self.session.add(user)
        await self.session.commit()

    async def update_user(self, id: int, data: UserUpdate) -> User | None:
        user = await self.session.get(User, id)
        if user is None:
            return None
        for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(user, field, value)
        await self.session.commit()
        await self.session.refresh(user)
        return user