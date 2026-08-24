import logging
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.repositories import NeonAuthUserRepository
from nexus_backend.database import get_db_session

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Valida la autenticación contra Neon Auth (Session Token o JWT) y obtiene el usuario."""
    token = credentials.credentials
    repo = NeonAuthUserRepository(session)

    # 1. Búsqueda directa por token de sesión en neon_auth.session
    user = await repo.get_by_session_token(token)
    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been suspended or banned.",
            )
        return user

    # 2. Si el token es un JWT, extraer el sujeto (UUID o email)
    try:
        unverified_payload = jwt.decode(token, options={"verify_signature": False})
        subject = unverified_payload.get("sub") or unverified_payload.get("userId")
        if subject:
            try:
                user_id = UUID(str(subject))
                user = await repo.get_by_id(user_id)
            except ValueError:
                user = await repo.get_by_email(str(subject))

            if user:
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Account has been suspended or banned.",
                    )
                return user
    except Exception as exc:
        logger.debug("Token could not be decoded as JWT: %s", exc)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials. Please authenticate via Neon Auth.",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Guardia RBAC que restringe el acceso exclusivamente a administradores."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin role required to perform this action.",
        )
    return current_user
