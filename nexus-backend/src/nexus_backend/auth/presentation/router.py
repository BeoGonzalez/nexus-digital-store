from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime, timezone

from nexus_backend.auth.application.dtos import (
    AuthInfoResponse,
    UserResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.models import NeonAuthUserModel
from nexus_backend.auth.infrastructure.security import JwtTokenIssuer
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.config import get_settings
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    # Mock login que busca al usuario en neon_auth y devuelve un JWT
    # ya que Neon Auth debería manejar las contraseñas, pero el frontend usa esta ruta.
    from sqlalchemy import select, func
    
    # Normalizar email
    clean_email = body.email.strip().lower()
    print(f"Intento de login para: '{clean_email}'")
    
    result = await session.execute(
        select(NeonAuthUserModel).where(func.lower(NeonAuthUserModel.email) == clean_email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"Usuario '{clean_email}' no encontrado en neon_auth.user")
        raise HTTPException(status_code=401, detail="Credenciales inválidas o cuenta no detectada.")
    
    token = JwtTokenIssuer().issue(str(user.email))
    return TokenResponse(token=token)

@router.post("/register", response_model=UserResponse)
async def register(body: RegisterRequest, session: AsyncSession = Depends(get_db_session)) -> UserResponse:
    # Mock register para insertar un usuario en neon_auth.user directamente
    from sqlalchemy import select, func
    
    clean_email = body.email.strip().lower()
    print(f"Intento de registro para: '{clean_email}'")
    
    result = await session.execute(
        select(NeonAuthUserModel).where(func.lower(NeonAuthUserModel.email) == clean_email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
        
    new_user = NeonAuthUserModel(
        id=uuid.uuid4(),
        name=body.name,
        email=clean_email,
        emailVerified=True,
        createdAt=datetime.now(timezone.utc),
        updatedAt=datetime.now(timezone.utc),
        role="user",
        banned=False,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return UserResponse(
        id=str(new_user.id),
        name=new_user.name,
        email=new_user.email,
        role=new_user.role or "user",
        is_admin=new_user.role == "admin",
        is_active=not new_user.banned,
        image=new_user.image,
    )


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
