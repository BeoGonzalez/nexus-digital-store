from sqlalchemy import Numeric, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from nexus_backend.shared.infrastructure.models import Base, TimestampMixin
from nexus_backend.config import get_settings

_settings = get_settings()


class ProductModel(TimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    specifications: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    embedding = mapped_column(Vector(_settings.EMBEDDING_DIMENSIONS), nullable=True)
