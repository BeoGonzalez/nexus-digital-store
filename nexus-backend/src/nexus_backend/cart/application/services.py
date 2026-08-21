from uuid import UUID

from fastapi import HTTPException, status

from nexus_backend.cart.domain.entities import Cart
from nexus_backend.cart.domain.ports import CartRepository
from nexus_backend.catalog.domain.ports import ProductRepository


class CartService:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository) -> None:
        self._cart_repo = cart_repo
        self._product_repo = product_repo

    async def get_cart(self, user_id: UUID) -> Cart:
        return await self._cart_repo.get_or_create_cart(user_id)

    async def add_item(self, user_id: UUID, product_id: UUID, quantity: int) -> Cart:
        product = await self._product_repo.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product.stock < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock. Available: {product.stock}",
            )

        cart = await self._cart_repo.get_or_create_cart(user_id)
        return await self._cart_repo.add_item(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=float(product.price),
        )

    async def remove_item(self, user_id: UUID, item_id: UUID) -> Cart:
        cart = await self._cart_repo.get_or_create_cart(user_id)
        return await self._cart_repo.remove_item(cart_id=cart.id, item_id=item_id)

    async def update_item_quantity(self, user_id: UUID, item_id: UUID, quantity: int) -> Cart:
        cart = await self._cart_repo.get_or_create_cart(user_id)
        return await self._cart_repo.update_item_quantity(
            cart_id=cart.id, item_id=item_id, quantity=quantity,
        )

    async def checkout(self, user_id: UUID) -> Cart:
        cart = await self._cart_repo.get_or_create_cart(user_id)
        if not cart.items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty",
            )

        for item in cart.items:
            success = await self._product_repo.update_stock(item.product_id, -item.quantity)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient stock for product {item.product_name}",
                )

        return await self._cart_repo.checkout(cart.id)
