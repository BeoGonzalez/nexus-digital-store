import enum

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from nexus_backend.shared.domain.entities import BaseEntity
from nexus_backend.catalog.domain.entities import VideoGame


class PaymentMethodType(str, enum.Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    TRANSFER = "TRANSFER"


@dataclass
class PaymentMethod(BaseEntity):
    user_id: UUID | None = None
    method_type: PaymentMethodType = PaymentMethodType.CREDIT_CARD
    card_last_4: str = ""
    card_brand: str = ""
    is_default: bool = False


class OrderStatus(str, enum.Enum):
    """Estados válidos para una orden — dominio cerrado.

    Usar un Enum en lugar de String libre evita dependencias
    funcionales transitivas: si status fuera un String y se añadiera
    un campo `status_description`, aparecería la DF
    status → status_description donde `status` no es superclave,
    violando BCNF.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderItem(BaseEntity):
    order_id: UUID | None = None
    video_game_id: UUID | None = None
    quantity: int = 0
    unit_price_clp: int = 0  # Historical frozen price (snapshot)
    video_game: VideoGame | None = None

    @property
    def subtotal(self) -> int:
        return self.quantity * self.unit_price_clp


@dataclass
class Order(BaseEntity):
    user_id: UUID | None = None
    total_amount_clp: int = 0
    status: OrderStatus = OrderStatus.PENDING
    idempotency_key: str | None = None
    items: list[OrderItem] = field(default_factory=list)

    def calculate_total(self) -> int:
        self.total_amount_clp = sum(item.subtotal for item in self.items)
        return self.total_amount_clp
