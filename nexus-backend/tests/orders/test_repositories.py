"""Pruebas unitarias para SQLAlchemyOrderRepository con validación de mapeo relacional anidado."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
import pytest

from nexus_backend.catalog.infrastructure.models import VideoGame as VideoGameModel
from nexus_backend.orders.domain.entities import Order as OrderEntity, OrderStatus
from nexus_backend.orders.infrastructure.models import OrderItemModel, OrderModel
from nexus_backend.orders.infrastructure.repositories import SQLAlchemyOrderRepository


class TestSQLAlchemyOrderRepository:
    """Suite de validación de persistencia y mapeo relacional ORM para órdenes."""

    @pytest.mark.asyncio
    async def test_to_entity_maps_nested_order_and_items_precisely(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyOrderRepository(mock_session)

        order_id = uuid4()
        user_id = str(uuid4())
        game_id = uuid4()
        now = datetime.now(timezone.utc)

        vg_model = VideoGameModel(
            id=game_id,
            title="Dark Souls III",
            description="Challenging action RPG",
            price_clp=29990,
            stock=12,
            genres=[],
        )
        item_model = OrderItemModel(
            id=uuid4(),
            order_id=order_id,
            video_game_id=game_id,
            quantity=2,
            unit_price_clp=29990,
            video_game=vg_model,
        )
        order_model = OrderModel(
            id=order_id,
            user_id=user_id,
            total_amount_clp=59980,
            status=OrderStatus.CONFIRMED,
            items=[item_model],
            created_at=now,
            updated_at=now,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = order_model
        mock_session.execute.return_value = mock_result

        # Act
        entity = await repo.get_by_id(order_id)

        # Assert - Mapeo relacional campo a campo sin tautología
        assert entity is not None
        assert isinstance(entity, OrderEntity)
        assert entity.id == order_id
        assert entity.user_id == user_id
        assert entity.total_amount_clp == 59980
        assert entity.status == OrderStatus.CONFIRMED
        assert len(entity.items) == 1

        entity_item = entity.items[0]
        assert entity_item.video_game_id == game_id
        assert entity_item.quantity == 2
        assert entity_item.unit_price_clp == 29990
        assert entity_item.subtotal == 59980
        assert entity_item.video_game is not None
        assert entity_item.video_game.title == "Dark Souls III"

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_when_missing(self) -> None:
        # Arrange
        mock_session = AsyncMock()
        repo = SQLAlchemyOrderRepository(mock_session)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Act
        result = await repo.get_by_id(uuid4())

        # Assert
        assert result is None
