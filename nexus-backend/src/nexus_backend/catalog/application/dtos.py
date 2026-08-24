from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class GenreResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class VideoGameResponse(BaseModel):
    id: UUID
    title: str
    description: str
    price_clp: int
    stock: int
    genres: list[GenreResponse]
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateVideoGameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    price_clp: int = Field(..., gt=0, description="Precio en pesos chilenos (debe ser positivo)")
    stock: int = Field(..., ge=0, description="Stock disponible no negativo")
    genre_names: list[str] = Field(default_factory=list)


class UpdateVideoGameRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    price_clp: int | None = Field(None, gt=0)
    stock: int | None = Field(None, ge=0)
    genre_names: list[str] | None = None


class DeleteVideoGameResponse(BaseModel):
    id: UUID
    success: bool
    message: str
