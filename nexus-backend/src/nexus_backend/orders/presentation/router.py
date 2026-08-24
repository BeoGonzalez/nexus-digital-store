from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.auth.domain.entities import User
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyVideoGameRepository
from nexus_backend.database import get_db_session
from nexus_backend.orders.application.dtos import CreateOrderRequest, OrderResponse, OrderItemResponse
from nexus_backend.orders.application.services import OrderService
from nexus_backend.orders.domain.entities import Order
from nexus_backend.orders.infrastructure.repositories import SQLAlchemyOrderRepository

router = APIRouter(prefix="/orders", tags=["Orders"])


def _get_order_service(session: AsyncSession = Depends(get_db_session)) -> OrderService:
    order_repo = SQLAlchemyOrderRepository(session)
    video_game_repo = SQLAlchemyVideoGameRepository(session)
    return OrderService(order_repo=order_repo, video_game_repo=video_game_repo)


def _to_response(order: Order) -> OrderResponse:
    from nexus_backend.catalog.presentation.router import _to_response as to_video_game_response
    
    items_resp = []
    for item in order.items:
        items_resp.append(
            OrderItemResponse(
                id=item.id,
                video_game_id=item.video_game_id,
                quantity=item.quantity,
                unit_price_clp=item.unit_price_clp,
                subtotal=item.subtotal,
                video_game=to_video_game_response(item.video_game) if item.video_game else None,
                created_at=item.created_at if hasattr(item, "created_at") else None,
            )
        )
        
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        total_amount_clp=order.total_amount_clp,
        status=order.status,
        items=items_resp,
        created_at=order.created_at if hasattr(order, "created_at") else None,
    )


@router.get("", response_model=list[OrderResponse])
async def get_user_orders(
    service: OrderService = Depends(_get_order_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    orders = await service.get_user_orders(current_user.id)
    return [_to_response(o) for o in orders]


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: CreateOrderRequest,
    service: OrderService = Depends(_get_order_service),
    current_user: User = Depends(get_current_user),
) -> Any:
    order = await service.create_order(current_user.id, body)
    return _to_response(order)
