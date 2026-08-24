from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nexus_backend.orders.domain.entities import Order as OrderEntity, OrderItem as OrderItemEntity
from nexus_backend.orders.domain.ports import OrderRepository
from nexus_backend.orders.infrastructure.models import OrderModel, OrderItemModel
from nexus_backend.catalog.domain.entities import VideoGame as VideoGameEntity, Genre as GenreEntity


class SQLAlchemyOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: OrderModel) -> OrderEntity:
        items = []
        for item_model in model.items:
            video_game = None
            if hasattr(item_model, "video_game") and item_model.video_game:
                vg_model = item_model.video_game
                video_game = VideoGameEntity(
                    id=vg_model.id,
                    title=vg_model.title,
                    description=vg_model.description,
                    price_clp=vg_model.price_clp,
                    stock=vg_model.stock,
                    embedding=vg_model.embedding if vg_model.embedding is not None else [],
                    genres=[GenreEntity(id=g.id, name=g.name) for g in vg_model.genres] if hasattr(vg_model, 'genres') else [],
                )
            
            items.append(
                OrderItemEntity(
                    id=item_model.id,
                    order_id=item_model.order_id,
                    video_game_id=item_model.video_game_id,
                    quantity=item_model.quantity,
                    unit_price_clp=item_model.unit_price_clp,
                    video_game=video_game
                )
            )
            
        return OrderEntity(
            id=model.id,
            user_id=model.user_id,
            total_amount_clp=model.total_amount_clp,
            status=model.status,
            items=items,
        )

    async def get_by_user_id(self, user_id: UUID) -> list[OrderEntity]:
        stmt = (
            select(OrderModel)
            .where(OrderModel.user_id == user_id)
            .options(selectinload(OrderModel.items).joinedload(OrderItemModel.video_game))
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().unique()]

    async def get_by_id(self, order_id: UUID) -> OrderEntity | None:
        stmt = (
            select(OrderModel)
            .where(OrderModel.id == order_id)
            .options(selectinload(OrderModel.items).joinedload(OrderItemModel.video_game))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, order: OrderEntity) -> OrderEntity:
        model = OrderModel(
            user_id=order.user_id,
            total_amount_clp=order.total_amount_clp,
            status=order.status,
            items=[
                OrderItemModel(
                    video_game_id=item.video_game_id,
                    quantity=item.quantity,
                    unit_price_clp=item.unit_price_clp
                )
                for item in order.items
            ]
        )
        self._session.add(model)
        await self._session.flush()
        
        # Reload to get the joined data
        return await self.get_by_id(model.id)
