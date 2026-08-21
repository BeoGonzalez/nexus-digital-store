from dataclasses import dataclass, field
from decimal import Decimal

from nexus_backend.shared.domain.entities import BaseEntity


@dataclass
class Product(BaseEntity):
    name: str = ""
    brand: str = ""
    category: str = ""
    description: str = ""
    price: Decimal = Decimal("0.00")
    stock: int = 0
    specifications: dict = field(default_factory=dict)
    image_url: str = ""
    embedding: list[float] | None = None
