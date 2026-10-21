"""Pruebas unitarias para SQLAlchemyVideoGameRepository con verificación de mapeo y excepciones de integridad."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest
from sqlalchemy.exc import IntegrityError

from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.catalog.infrastructure.models import Genre as GenreModel, VideoGame as VideoGameModel
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyVideoGameRepository
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException


class TestSQLAlchemyVideoGameRepository:
    """Suite de validación de persistencia y mapeo ORM para el catálogo."""

    @pytest.mark.asyncio
    async def test_to_entity_maps_orm_model_precisely(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyVideoGameRepository(mock_session)

        game_id = uuid4()
        now = datetime.now(timezone.utc)
        genre_model = GenreModel(id=uuid4(), name="Soulslike")
        orm_model = VideoGameModel(
            id=game_id,
            title="Dark Souls III",
            description="Challenging action RPG",
            price_clp=29990,
            stock=12,
            genres=[genre_model],
            created_at=now,
            updated_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = orm_model
        mock_session.execute.return_value = mock_result

        # Act
        entity = await repo.get_by_id(game_id)

        # Assert - Mapeo estricto campo a campo
        assert entity is not None
        assert isinstance(entity, VideoGame)
        assert entity.id == game_id
        assert entity.title == "Dark Souls III"
        assert entity.description == "Challenging action RPG"
        assert entity.price_clp == 29990
        assert entity.stock == 12
        assert entity.embedding == []
        assert len(entity.genres) == 1
        assert entity.genres[0].name == "Soulslike"
        assert entity.created_at == now
        assert entity.updated_at == now

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyVideoGameRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repo.get_by_id(uuid4())

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_with_foreign_key_violation_catches_integrity_error_and_rolls_back(
        self,
    ) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyVideoGameRepository(mock_session)
        game_id = uuid4()

        # Simular que SQLAlchemy lanza IntegrityError por la FK order_items_video_game_id_fkey
        orig_err = Exception("update or delete violates foreign key constraint")
        mock_session.execute.side_effect = IntegrityError(
            statement="DELETE FROM video_games", params={}, orig=orig_err
        )

        # Act & Assert
        # Regla de persistencia: El repositorio debe atrapar el IntegrityError,
        # realizar rollback en la sesión y propagar un BusinessRuleViolationException descriptivo.
        with pytest.raises(BusinessRuleViolationException) as exc_info:
            await repo.delete(game_id)

        assert str(game_id) in str(exc_info.value)
        assert "referenced in existing customer orders" in str(exc_info.value)
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_stock_success_returns_true_when_rows_affected(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyVideoGameRepository(mock_session)

        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        # Act
        success = await repo.update_stock(uuid4(), -2)

        # Assert
        assert success is True

    @pytest.mark.asyncio
    async def test_update_stock_fails_when_zero_rows_affected(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyVideoGameRepository(mock_session)

        mock_result = MagicMock()
        mock_result.rowcount = 0  # Condición where stock + change >= 0 no se cumplió
        mock_session.execute.return_value = mock_result

        # Act
        success = await repo.update_stock(uuid4(), -100)

        # Assert
        assert success is False
