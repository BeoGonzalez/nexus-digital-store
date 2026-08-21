from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.repositories import SQLAlchemyUserRepository
from nexus_backend.auth.infrastructure.security import decode_jwt_token
from nexus_backend.database import get_db_session

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_jwt_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    repo = SQLAlchemyUserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user
