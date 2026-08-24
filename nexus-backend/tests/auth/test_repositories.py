"""Pruebas unitarias para NeonAuthUserRepository con aserciones estrictas de mapeo y contratos SQL."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.models import NeonAuthSessionModel, NeonAuthUserModel
from nexus_backend.auth.infrastructure.repositories import NeonAuthUserRepository


class TestNeonAuthUserRepository:
    """Suite de validación de la capa de persistencia para Neon Auth."""

    @pytest.mark.asyncio
    async def test_get_by_id_maps_entity_fields_precisely(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = NeonAuthUserRepository(mock_session)

        user_id = uuid4()
        now = datetime.now(timezone.utc)
        fake_db_model = NeonAuthUserModel(
            id=user_id,
            name="Gamer Pro",
            email="pro@nexus.cl",
            emailVerified=True,
            image="https://cdn.nexus.cl/avatar.png",
            createdAt=now,
            updatedAt=now,
            role="admin",
            banned=False,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_db_model
        mock_session.execute.return_value = mock_result

        # Act
        result_user = await repo.get_by_id(user_id)

        # Assert - Mapeo estricto campo a campo sin tautología
        assert result_user is not None
        assert isinstance(result_user, User)
        assert result_user.id == user_id
        assert result_user.name == "Gamer Pro"
        assert result_user.email == "pro@nexus.cl"
        assert result_user.role == "admin"
        assert result_user.is_admin is True
        assert result_user.banned is False
        assert result_user.is_active is True
        assert result_user.email_verified is True
        assert result_user.image == "https://cdn.nexus.cl/avatar.png"
        assert result_user.created_at == now
        assert result_user.updated_at == now

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_record_missing(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = NeonAuthUserRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repo.get_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_session_token_retrieves_user_via_relation(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = NeonAuthUserRepository(mock_session)

        now = datetime.now(timezone.utc)
        fake_user_model = NeonAuthUserModel(
            id=uuid4(),
            name="Session User",
            email="session@nexus.cl",
            emailVerified=True,
            createdAt=now,
            updatedAt=now,
            role="user",
            banned=False,
        )
        fake_session_model = NeonAuthSessionModel(
            id=uuid4(),
            token="active_session_abc",
            userId=fake_user_model.id,
            expiresAt=now,
            createdAt=now,
            updatedAt=now,
            user=fake_user_model,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = fake_session_model
        mock_session.execute.return_value = mock_result

        # Act
        result_user = await repo.get_by_session_token("active_session_abc")

        # Assert
        assert result_user is not None
        assert result_user.id == fake_user_model.id
        assert result_user.email == "session@nexus.cl"
        assert result_user.role == "user"

    @pytest.mark.asyncio
    async def test_get_by_session_token_returns_none_when_expired_or_invalid(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = NeonAuthUserRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result_user = await repo.get_by_session_token("expired_or_missing_token")

        # Assert
        assert result_user is None
