from fastapi import HTTPException, status

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.domain.ports import UserRepository
from nexus_backend.auth.infrastructure.security import (
    create_jwt_token,
    hash_password,
    verify_password,
)


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(self, email: str, password: str, full_name: str) -> User:
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
        )
        return await self._user_repo.create(user)

    async def authenticate(self, email: str, password: str) -> str:
        user = await self._user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated",
            )
        return create_jwt_token(subject=str(user.id))
