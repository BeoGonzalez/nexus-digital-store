from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from nexus_backend.shared.domain.entities import BaseEntity


class CartStatus(StrEnum):
    ACTIVE = "active"
    CHECKED_OUT = "checked_out"


@dataclass
class CartItem:
    id: UUID = field(default_factory=lambda: __import__("uuid").uuid4())
    product_id: UUID = field(default_factory=lambda: __import__("uuid").uuid4())
    product_name: str = ""
    quantity: int = 1
    unit_price: Decimal = Decimal("0.00")

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass
class Cart(BaseEntity):
    user_id: UUID = field(default_factory=lambda: __import__("uuid").uuid4())
    status: CartStatus = CartStatus.ACTIVE
    items: list[CartItem] = field(default_factory=list)

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0.00"))
