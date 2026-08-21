from decimal import Decimal

from pydantic import BaseModel


class ProductCreateRequest(BaseModel):
    name: str
    brand: str
    category: str
    description: str
    price: Decimal
    stock: int
    specifications: dict = {}
    image_url: str = ""


class ProductResponse(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    description: str
    price: Decimal
    stock: int
    specifications: dict
    image_url: str

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
