from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class AddToCartRequest(BaseModel):
    product_id: UUID
    quantity: int = 1


class UpdateCartItemRequest(BaseModel):
    quantity: int


class CartItemResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    id: str
    status: str
    items: list[CartItemResponse]
    total: Decimal

    model_config = {"from_attributes": True}
