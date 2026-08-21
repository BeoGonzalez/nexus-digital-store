import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nexus_backend.shared.infrastructure.models import Base, TimestampMixin


class CartItemModel(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id"), nullable=False,
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    cart: Mapped["CartModel"] = relationship(back_populates="items")


class CartModel(TimestampMixin, Base):
    __tablename__ = "carts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    items: Mapped[list[CartItemModel]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
