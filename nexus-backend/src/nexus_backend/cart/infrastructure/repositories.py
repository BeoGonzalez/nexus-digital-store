from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.cart.domain.entities import Cart, CartItem, CartStatus
from nexus_backend.cart.infrastructure.models import CartItemModel, CartModel


class SQLAlchemyCartRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_active_cart(self, user_id: UUID) -> Cart | None:
        result = await self._session.execute(
            select(CartModel).where(
                CartModel.user_id == user_id,
                CartModel.status == CartStatus.ACTIVE,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        cart = await self.get_active_cart(user_id)
        if cart:
            return cart

        model = CartModel(user_id=user_id, status=CartStatus.ACTIVE)
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def add_item(
        self, cart_id: UUID, product_id: UUID, quantity: int, unit_price: float,
    ) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.id == cart_id)
        )
        cart_model = result.scalar_one()

        existing = next(
            (i for i in cart_model.items if i.product_id == product_id), None,
        )
        if existing:
            existing.quantity += quantity
        else:
            from nexus_backend.catalog.infrastructure.models import ProductModel

            prod_result = await self._session.execute(
                select(ProductModel.name).where(ProductModel.id == product_id)
            )
            product_name = prod_result.scalar_one()

            item = CartItemModel(
                cart_id=cart_id,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
            )
            self._session.add(item)

        await self._session.flush()
        await self._session.refresh(cart_model)
        return self._to_entity(cart_model)

    async def remove_item(self, cart_id: UUID, item_id: UUID) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.id == cart_id)
        )
        cart_model = result.scalar_one()
        cart_model.items = [i for i in cart_model.items if i.id != item_id]
        await self._session.flush()
        await self._session.refresh(cart_model)
        return self._to_entity(cart_model)

    async def update_item_quantity(self, cart_id: UUID, item_id: UUID, quantity: int) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.id == cart_id)
        )
        cart_model = result.scalar_one()
        for item in cart_model.items:
            if item.id == item_id:
                item.quantity = quantity
                break
        await self._session.flush()
        await self._session.refresh(cart_model)
        return self._to_entity(cart_model)

    async def checkout(self, cart_id: UUID) -> Cart:
        result = await self._session.execute(
            select(CartModel).where(CartModel.id == cart_id)
        )
        cart_model = result.scalar_one()
        cart_model.status = CartStatus.CHECKED_OUT
        await self._session.flush()
        return self._to_entity(cart_model)

    @staticmethod
    def _to_entity(model: CartModel) -> Cart:
        return Cart(
            id=model.id,
            user_id=model.user_id,
            status=CartStatus(model.status),
            items=[
                CartItem(
                    id=i.id,
                    product_id=i.product_id,
                    product_name=i.product_name,
                    quantity=i.quantity,
                    unit_price=Decimal(str(i.unit_price)),
                )
                for i in model.items
            ],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
