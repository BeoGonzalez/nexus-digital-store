"""Pruebas unitarias para OrderService con verificación de cálculos matemáticos, atomicidad y caminos infelices."""

from unittest.mock import AsyncMock, call
from uuid import UUID, uuid4
import pytest

from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.orders.application.dtos import CreateOrderRequest, OrderItemRequest
from nexus_backend.orders.application.services import OrderService
from nexus_backend.orders.domain.entities import Order, OrderStatus
from nexus_backend.shared.domain.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
)


@pytest.fixture
def order_service(mock_order_repo: AsyncMock, mock_video_game_repo: AsyncMock) -> OrderService:
    return OrderService(order_repo=mock_order_repo, video_game_repo=mock_video_game_repo)


class TestOrderService:
    """Suite de validación de lógica transaccional y reglas de negocio de órdenes."""

    @pytest.mark.asyncio
    async def test_create_order_happy_path_calculates_total_and_updates_stock_atomically(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        user_id = uuid4()
        game1 = VideoGame(id=uuid4(), title="Elden Ring", price_clp=39990, stock=10)
        game2 = VideoGame(id=uuid4(), title="Hollow Knight", price_clp=12990, stock=5)

        async def fake_get_by_id(vid: UUID) -> VideoGame | None:
            if vid == game1.id:
                return game1
            if vid == game2.id:
                return game2
            return None

        mock_video_game_repo.get_by_id.side_effect = fake_get_by_id
        mock_video_game_repo.update_stock.return_value = True
        mock_order_repo.create.side_effect = lambda o: o

        request = CreateOrderRequest(
            items=[
                OrderItemRequest(video_game_id=game1.id, quantity=2),  # 2 * 39990 = 79980
                OrderItemRequest(video_game_id=game2.id, quantity=1),  # 1 * 12990 = 12990
            ]
        )

        # Act
        created_order = await order_service.create_order(user_id, request)

        # Assert - Spying y contratos de comunicación
        # 1. Verificación de llamadas atómicas a update_stock con cantidades negativas exactas
        assert mock_video_game_repo.update_stock.call_count == 2
        mock_video_game_repo.update_stock.assert_has_calls(
            [call(game1.id, -2), call(game2.id, -1)],
            any_order=False,
        )

        # 2. Verificación de captura del argumento enviado a order_repo.create
        mock_order_repo.create.assert_called_once()
        persisted_order: Order = mock_order_repo.create.call_args[0][0]

        # 3. Verificación matemática exacta del total calculado (79980 + 12990 = 92970)
        assert persisted_order.total_amount_clp == 92970
        assert persisted_order.user_id == user_id
        assert persisted_order.status == OrderStatus.PENDING
        assert len(persisted_order.items) == 2

        # 4. Verificación de snapshots de precios congelados en los ítems
        item1 = persisted_order.items[0]
        assert item1.video_game_id == game1.id
        assert item1.quantity == 2
        assert item1.unit_price_clp == 39990
        assert item1.subtotal == 79980

        item2 = persisted_order.items[1]
        assert item2.video_game_id == game2.id
        assert item2.quantity == 1
        assert item2.unit_price_clp == 12990
        assert item2.subtotal == 12990

    @pytest.mark.asyncio
    async def test_create_order_empty_items_raises_business_rule_violation(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        user_id = uuid4()
        empty_request = CreateOrderRequest(items=[])

        # Act & Assert
        # Regla de negocio: No se puede generar una orden vacía
        with pytest.raises(BusinessRuleViolationException, match="Cannot create an empty order."):
            await order_service.create_order(user_id, empty_request)

        mock_video_game_repo.update_stock.assert_not_called()
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_missing_video_game_raises_not_found(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        user_id = uuid4()
        missing_game_id = uuid4()
        mock_video_game_repo.get_by_id.return_value = None

        request = CreateOrderRequest(
            items=[OrderItemRequest(video_game_id=missing_game_id, quantity=1)]
        )

        # Act & Assert
        with pytest.raises(ResourceNotFoundException, match=f"Video game {missing_game_id} not found."):
            await order_service.create_order(user_id, request)

        mock_video_game_repo.update_stock.assert_not_called()
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock_raises_business_rule_violation_and_aborts(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        user_id = uuid4()
        dummy_video_game.stock = 3
        mock_video_game_repo.get_by_id.return_value = dummy_video_game

        # El cliente solicita 5 unidades cuando solo hay 3 disponibles
        request = CreateOrderRequest(
            items=[OrderItemRequest(video_game_id=dummy_video_game.id, quantity=5)]
        )

        # Act & Assert
        # Regla de negocio: Si no hay stock suficiente, debe abortar de inmediato sin mutar la BD
        with pytest.raises(BusinessRuleViolationException, match="Not enough stock"):
            await order_service.create_order(user_id, request)

        mock_video_game_repo.update_stock.assert_not_called()
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_atomic_stock_race_condition_failure_raises_business_rule_violation(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        user_id = uuid4()
        dummy_video_game.stock = 10
        mock_video_game_repo.get_by_id.return_value = dummy_video_game
        # update_stock retorna False si otra transacción concurrente consumió el stock en el UPDATE SQL
        mock_video_game_repo.update_stock.return_value = False

        request = CreateOrderRequest(
            items=[OrderItemRequest(video_game_id=dummy_video_game.id, quantity=2)]
        )

        # Act & Assert
        with pytest.raises(BusinessRuleViolationException, match="Failed to secure stock"):
            await order_service.create_order(user_id, request)

        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_orders_passes_user_id_strictly(
        self,
        order_service: OrderService,
        mock_order_repo: AsyncMock,
        dummy_order: Order,
    ) -> None:
        # Arrange
        user_id = uuid4()
        mock_order_repo.get_by_user_id.return_value = [dummy_order]

        # Act
        orders = await order_service.get_user_orders(user_id)

        # Assert
        mock_order_repo.get_by_user_id.assert_called_once_with(user_id)
        assert orders == [dummy_order]
