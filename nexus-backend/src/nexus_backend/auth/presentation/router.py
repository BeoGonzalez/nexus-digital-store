"""Endpoints de autenticación e identidad de usuario (Amazon Cognito)."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, status

from nexus_backend.auth.application.dtos import (
    AuthInfoResponse,
    UserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier, get_cognito_verifier
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    verifier: CognitoTokenVerifier = Depends(get_cognito_verifier),
) -> TokenResponse:
    """Inicia sesión autenticando al usuario contra Amazon Cognito User Pool y retorna el JWT Bearer."""
    token = await verifier.authenticate_user(body.email, body.password)
    return TokenResponse(token=token)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    verifier: CognitoTokenVerifier = Depends(get_cognito_verifier),
) -> UserResponse:
    """Registra un nuevo usuario en Amazon Cognito User Pool."""
    result = await verifier.register_user(body.email, body.password, body.name)
    sub = result.get("UserSub") or ""
    return UserResponse(
        id=sub,
        name=body.name,
        email=body.email,
        role="user",
        is_admin=False,
        is_active=True,
        image=None,
    )


@router.get("/info", response_model=AuthInfoResponse)
async def auth_info() -> AuthInfoResponse:
    """Retorna los datos de configuración pública de autenticación con Amazon Cognito."""
    return AuthInfoResponse(
        auth_provider="Amazon Cognito",
        cognito_region=settings.COGNITO_REGION,
        cognito_user_pool_id=settings.COGNITO_USER_POOL_ID,
        cognito_app_client_id=settings.COGNITO_APP_CLIENT_ID,
        message="Authentication and user management are strictly handled by Amazon Cognito.",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Obtiene los datos del usuario autenticado actual a partir de su JWT de Cognito."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        image=current_user.image,
    )
