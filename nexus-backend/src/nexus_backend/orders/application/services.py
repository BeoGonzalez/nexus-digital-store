from uuid import UUID

from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.orders.application.dtos import CreateOrderRequest
from nexus_backend.orders.domain.entities import Order, OrderItem, OrderStatus
from nexus_backend.orders.domain.ports import OrderRepository
from nexus_backend.shared.domain.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
)


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        video_game_repo: VideoGameRepository,
    ) -> None:
        self._order_repo = order_repo
        self._video_game_repo = video_game_repo

    async def get_user_orders(self, user_id: str) -> list[Order]:
        return await self._order_repo.get_by_user_id(user_id)

    async def create_order(self, user_id: str, request: CreateOrderRequest, idempotency_key: str | None = None) -> Order:
        if idempotency_key:
            existing_order = await self._order_repo.get_by_idempotency_key(idempotency_key)
            if existing_order:
                return existing_order

        if not request.items:
            raise BusinessRuleViolationException("Cannot create an empty order.")

        order_items = []
        for item_req in request.items:
            video_game = await self._video_game_repo.get_by_id(item_req.video_game_id)
            if not video_game:
                raise ResourceNotFoundException(f"Video game {item_req.video_game_id} not found.")
            
            if video_game.stock < item_req.quantity:
                raise BusinessRuleViolationException(f"Not enough stock for video game '{video_game.title}'.")
            
            # Atomic stock update
            stock_updated = await self._video_game_repo.update_stock(
                video_game.id, -item_req.quantity
            )
            if not stock_updated:
                raise BusinessRuleViolationException(
                    f"Failed to secure stock for video game '{video_game.title}'."
                )

            order_item = OrderItem(
                video_game_id=video_game.id,
                quantity=item_req.quantity,
                unit_price_clp=video_game.price_clp,
                video_game=video_game,
            )
            order_items.append(order_item)

        order = Order(
            user_id=user_id,
            items=order_items,
            status=OrderStatus.PENDING,
            idempotency_key=idempotency_key,
        )
        order.calculate_total()
        
        return await self._order_repo.create(order)


class PaymentMethodService:
    def __init__(self, payment_repo: "PaymentMethodRepository") -> None:
        self._payment_repo = payment_repo

    async def get_user_payment_methods(self, user_id: str) -> list["PaymentMethod"]:
        return await self._payment_repo.get_by_user_id(user_id)

    async def add_payment_method(self, user_id: str, request: "CreatePaymentMethodRequest") -> "PaymentMethod":
        from nexus_backend.orders.domain.entities import PaymentMethod
        
        # Simulamos que tomamos los últimos 4 dígitos reales de un token
        last_4 = request.card_number[-4:] if len(request.card_number) >= 4 else "0000"
        
        pm = PaymentMethod(
            user_id=user_id,
            card_last_4=last_4,
            card_brand=request.card_brand,
            is_default=request.is_default,
        )
        return await self._payment_repo.create(pm)
