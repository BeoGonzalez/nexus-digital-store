import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nexus_backend.shared.infrastructure.models import Base, TimestampMixin
from nexus_backend.orders.domain.entities import OrderStatus


# ──────────────────────────────────────────────────────────────
# Order — Cabecera de la orden de compra
# ──────────────────────────────────────────────────────────────
# BCNF: {id} → {user_id, total_amount_clp, status, ...}
# Única clave candidata: `id` (PK). Toda DF no trivial tiene
# como determinante a `id`, que es superclave.
#
# `status` usa pgEnum nativo, no String libre, para cerrar el
# dominio y prevenir DFs transitivas futuras.
# ──────────────────────────────────────────────────────────────
class OrderModel(TimestampMixin, Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint(
            "total_amount_clp >= 0",
            name="ck_orders_non_negative_total",
        ),
    )

    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
    )
    total_amount_clp: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            name="order_status",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
            create_constraint=False,
            native_enum=True,
        ),
        default=OrderStatus.PENDING,
        server_default=OrderStatus.PENDING.value,
        nullable=False,
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)

    items: Mapped[list["OrderItemModel"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Order {self.id} status={self.status.value}>"


# ──────────────────────────────────────────────────────────────
# OrderItem — Línea de detalle de la orden
# ──────────────────────────────────────────────────────────────
# BCNF: {id} → {order_id, video_game_id, quantity, unit_price_clp}
# Única clave candidata: `id` (PK).
#
# NOTA CRÍTICA sobre `unit_price_clp` (snapshot):
# Este campo congela el precio al momento de la compra.
# NO es funcionalmente dependiente de `video_game_id`:
#   video_game_id ↛ unit_price_clp
# porque dos OrderItems con el mismo video_game_id pueden tener
# distinto unit_price_clp si el precio del catálogo cambió.
# Esto preserva BCNF y garantiza aislamiento histórico.
# ──────────────────────────────────────────────────────────────
class OrderItemModel(TimestampMixin, Base):
    __tablename__ = "order_items"
    __table_args__ = (
        UniqueConstraint("order_id", "video_game_id", name="uq_order_items_order_game"),
        CheckConstraint("quantity > 0", name="ck_order_items_positive_quantity"),
        CheckConstraint("unit_price_clp > 0", name="ck_order_items_positive_price"),
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    video_game_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("video_games.id", ondelete="RESTRICT"), nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_clp: Mapped[int] = mapped_column(Integer, nullable=False)

    order: Mapped["OrderModel"] = relationship(back_populates="items")
    video_game = relationship("VideoGame", lazy="joined")

    def __repr__(self) -> str:
        return f"<OrderItem game={self.video_game_id} qty={self.quantity}>"


# ──────────────────────────────────────────────────────────────
# PaymentMethod — Métodos de pago (Tarjetas guardadas)
# ──────────────────────────────────────────────────────────────
# BCNF: {id} → {user_id, card_last_4, card_brand, is_default}
# Única clave candidata: `id` (PK). 
# ──────────────────────────────────────────────────────────────
class PaymentMethodModel(TimestampMixin, Base):
    __tablename__ = "payment_methods"

    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True,
    )
    method_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="CREDIT_CARD")
    card_last_4: Mapped[str] = mapped_column(String(4), nullable=False)
    card_brand: Mapped[str] = mapped_column(String(50), nullable=False)
    is_default: Mapped[bool] = mapped_column(default=False, server_default="false", nullable=False)

    def __repr__(self) -> str:
        return f"<PaymentMethod user={self.user_id} last4={self.card_last_4}>"
