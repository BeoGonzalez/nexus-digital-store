from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.application.dtos import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from nexus_backend.auth.application.services import AuthService
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.repositories import SQLAlchemyUserRepository
from nexus_backend.auth.infrastructure.security import JwtTokenIssuer, PasslibPasswordHasher
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    return AuthService(
        user_repo=SQLAlchemyUserRepository(session),
        password_hasher=PasslibPasswordHasher(),
        token_issuer=JwtTokenIssuer(),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(_get_auth_service),
) -> UserResponse:
    user = await service.register(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
    )
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(_get_auth_service),
) -> TokenResponse:
    token = await service.authenticate(email=body.email, password=body.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
    )
