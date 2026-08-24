from fastapi import APIRouter, Depends

from nexus_backend.auth.application.dtos import AuthInfoResponse, UserResponse
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.get("/info", response_model=AuthInfoResponse)
async def auth_info() -> AuthInfoResponse:
    """Retorna los datos de conexión y endpoints de Neon Auth."""
    return AuthInfoResponse(
        neon_auth_url=settings.NEON_AUTH_URL,
        message="Authentication and user management are strictly handled by Neon Auth.",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Obtiene los datos del usuario autenticado actual a partir de su sesión de Neon Auth."""
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        is_admin=current_user.is_admin,
        is_active=current_user.is_active,
        image=current_user.image,
    )
