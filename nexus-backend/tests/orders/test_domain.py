"""Pruebas unitarias para las entidades del dominio de Órdenes (Invariantes y cálculos matemáticos)."""

from uuid import uuid4
import pytest

from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.orders.domain.entities import Order, OrderItem, OrderStatus


class TestOrderDomainEntities:
    """Suite de validación de invariantes de negocio y precisión matemática en órdenes."""

    @pytest.mark.parametrize(
        ("quantity", "unit_price", "expected_subtotal"),
        [
            (1, 49990, 49990),
            (3, 19990, 59970),
            (10, 5000, 50000),
            (0, 35000, 0),
        ],
    )
    def test_order_item_subtotal_calculation_is_exact(
        self, quantity: int, unit_price: int, expected_subtotal: int
    ) -> None:
        # Arrange
        item = OrderItem(
            id=uuid4(),
            video_game_id=uuid4(),
            quantity=quantity,
            unit_price_clp=unit_price,
        )

        # Act
        subtotal = item.subtotal

        # Assert
        # Regla de negocio: El subtotal de un ítem debe ser exactamente quantity * unit_price_clp
        assert subtotal == expected_subtotal

    def test_order_calculate_total_aggregates_items_and_mutates_state(self) -> None:
        # Arrange
        item1 = OrderItem(video_game_id=uuid4(), quantity=2, unit_price_clp=25000)  # subtotal = 50000
        item2 = OrderItem(video_game_id=uuid4(), quantity=1, unit_price_clp=39990)  # subtotal = 39990
        item3 = OrderItem(video_game_id=uuid4(), quantity=3, unit_price_clp=10000)  # subtotal = 30000

        order = Order(
            id=uuid4(),
            user_id=uuid4(),
            status=OrderStatus.PENDING,
            items=[item1, item2, item3],
        )

        # Act
        calculated_total = order.calculate_total()

        # Assert - Validación matemática y mutación del estado de la entidad
        assert calculated_total == 119990
        assert order.total_amount_clp == 119990

    def test_historical_price_snapshot_isolation(self) -> None:
        # Arrange
        game = VideoGame(id=uuid4(), title="Zelda", price_clp=45000, stock=10)
        item = OrderItem(
            id=uuid4(),
            video_game_id=game.id,
            quantity=1,
            unit_price_clp=game.price_clp,  # Snapshot histórico congelado
            video_game=game,
        )
        order = Order(id=uuid4(), user_id=uuid4(), items=[item])
        order.calculate_total()
        assert order.total_amount_clp == 45000

        # Act - El precio del juego cambia en el catálogo en el futuro (ej. oferta o inflación)
        game.price_clp = 60000

        # Assert
        # Regla BCNF / Negocio: El snapshot histórico congelado en la orden no debe alterarse
        assert item.unit_price_clp == 45000
        assert item.subtotal == 45000
        assert order.calculate_total() == 45000

    @pytest.mark.parametrize(
        "status_enum",
        [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ],
    )
    def test_order_status_enum_values_are_lowercase_strings(
        self, status_enum: OrderStatus
    ) -> None:
        # Assert - Validación de compatibilidad con PostgreSQL ENUM nativo y BCNF
        assert isinstance(status_enum.value, str)
        assert status_enum.value == status_enum.value.lower()
