from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from nexus_backend.catalog.application.dtos import VideoGameResponse


class OrderItemRequest(BaseModel):
    video_game_id: UUID
    quantity: int = Field(..., gt=0)


class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest]


class CreatePaymentMethodRequest(BaseModel):
    card_number: str = Field(..., description="Número de tarjeta completo (simulado)")
    card_brand: str = Field(..., description="Visa, Mastercard, AMEX, etc.")
    is_default: bool = False


class PaymentMethodResponse(BaseModel):
    id: UUID
    user_id: str
    card_last_4: str
    card_brand: str
    is_default: bool

    model_config = {"from_attributes": True}


class OrderItemResponse(BaseModel):
    id: UUID
    video_game_id: UUID
    quantity: int
    unit_price_clp: int
    subtotal: int
    video_game: VideoGameResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    user_id: str
    total_amount_clp: int
    status: str
    items: list[OrderItemResponse]
    created_at: datetime

    model_config = {"from_attributes": True}
