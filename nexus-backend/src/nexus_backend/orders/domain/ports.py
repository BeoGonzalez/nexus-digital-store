from typing import Protocol
from uuid import UUID

from nexus_backend.orders.domain.entities import Order


class OrderRepository(Protocol):
    async def get_by_user_id(self, user_id: UUID) -> list[Order]: ...
    async def get_by_id(self, order_id: UUID) -> Order | None: ...
    async def create(self, order: Order) -> Order: ...
