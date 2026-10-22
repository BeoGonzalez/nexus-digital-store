"""Seguridad y dependencias de autenticación basadas en Amazon Cognito."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier, get_cognito_verifier

logger = logging.getLogger(__name__)
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    verifier: CognitoTokenVerifier = Depends(get_cognito_verifier),
) -> User:
    """Valida la autenticación contra Amazon Cognito User Pool validando el Bearer JWT."""
    token = credentials.credentials
    user = await verifier.verify_token(token)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been suspended or banned.",
        )
    return user


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
