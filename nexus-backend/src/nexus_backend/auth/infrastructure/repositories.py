from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.models import NeonAuthUserModel, NeonAuthSessionModel


class NeonAuthUserRepository:
    """Repositorio para interactuar directamente con las tablas de Neon Auth."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(NeonAuthUserModel).where(NeonAuthUserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(NeonAuthUserModel).where(NeonAuthUserModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_session_token(self, token: str) -> User | None:
        """Busca una sesión activa en neon_auth.session y retorna el usuario asociado."""
        now = datetime.now(timezone.utc)
        stmt = (
            select(NeonAuthSessionModel)
            .where(
                NeonAuthSessionModel.token == token,
                NeonAuthSessionModel.expiresAt > now,
            )
        )
        result = await self._session.execute(stmt)
        session_model = result.scalar_one_or_none()
        if not session_model or not session_model.user:
            return None
        return self._to_entity(session_model.user)

    @staticmethod
    def _to_entity(model: NeonAuthUserModel) -> User:
        return User(
            id=model.id,
            name=model.name,
            email=model.email,
            role=model.role or "user",
            banned=bool(model.banned),
            email_verified=bool(model.emailVerified),
            image=model.image,
            created_at=model.createdAt,
            updated_at=model.updatedAt,
        )


# Alias para compatibilidad
SQLAlchemyUserRepository = NeonAuthUserRepository
