from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.cart.application.dtos import (
    AddToCartRequest,
    CartItemResponse,
    CartResponse,
    UpdateCartItemRequest,
)
from nexus_backend.cart.application.services import CartService
from nexus_backend.cart.domain.entities import Cart
from nexus_backend.cart.infrastructure.repositories import SQLAlchemyCartRepository
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyProductRepository
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/cart", tags=["Cart"])


def _get_cart_service(session: AsyncSession = Depends(get_db_session)) -> CartService:
    return CartService(
        cart_repo=SQLAlchemyCartRepository(session),
        product_repo=SQLAlchemyProductRepository(session),
    )


@router.get("", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(_get_cart_service),
) -> CartResponse:
    cart = await service.get_cart(current_user.id)
    return _to_response(cart)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
async def add_item(
    body: AddToCartRequest,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(_get_cart_service),
) -> CartResponse:
    cart = await service.add_item(
        user_id=current_user.id,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    return _to_response(cart)


@router.put("/items/{item_id}", response_model=CartResponse)
async def update_item(
    item_id: UUID,
    body: UpdateCartItemRequest,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(_get_cart_service),
) -> CartResponse:
    cart = await service.update_item_quantity(
        user_id=current_user.id,
        item_id=item_id,
        quantity=body.quantity,
    )
    return _to_response(cart)


@router.delete("/items/{item_id}", response_model=CartResponse)
async def remove_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(_get_cart_service),
) -> CartResponse:
    cart = await service.remove_item(user_id=current_user.id, item_id=item_id)
    return _to_response(cart)


@router.post("/checkout", response_model=CartResponse)
async def checkout(
    current_user: User = Depends(get_current_user),
    service: CartService = Depends(_get_cart_service),
) -> CartResponse:
    cart = await service.checkout(user_id=current_user.id)
    return _to_response(cart)


def _to_response(cart: Cart) -> CartResponse:
    return CartResponse(
        id=str(cart.id),
        status=cart.status.value,
        items=[
            CartItemResponse(
                id=str(item.id),
                product_id=str(item.product_id),
                product_name=item.product_name,
                quantity=item.quantity,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for item in cart.items
        ],
        total=cart.total,
    )
