import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nexus_backend.shared.infrastructure.models import Base


# ──────────────────────────────────────────────────────────────
# Neon Auth User — Mapeado al schema 'neon_auth.user'
# ──────────────────────────────────────────────────────────────
# Neon Auth es la fuente única de verdad de usuarios y roles.
# ──────────────────────────────────────────────────────────────
class NeonAuthUserModel(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "neon_auth"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    emailVerified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image: Mapped[str | None] = mapped_column(Text, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    role: Mapped[str | None] = mapped_column(Text, default="user", nullable=True)
    banned: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    banReason: Mapped[str | None] = mapped_column(Text, nullable=True)
    banExpires: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["NeonAuthSessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select",
    )
    orders: Mapped[list["OrderModel"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan", lazy="select",
    )

    def __repr__(self) -> str:
        return f"<NeonAuthUser {self.email} role={self.role}>"


# Alias para retrocompatibilidad
UserModel = NeonAuthUserModel


# ──────────────────────────────────────────────────────────────
# Neon Auth Session — Mapeado al schema 'neon_auth.session'
# ──────────────────────────────────────────────────────────────
class NeonAuthSessionModel(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "neon_auth"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    token: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    userId: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("neon_auth.user.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    expiresAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updatedAt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ipAddress: Mapped[str | None] = mapped_column(Text, nullable=True)
    userAgent: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["NeonAuthUserModel"] = relationship(
        back_populates="sessions", lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<NeonAuthSession token={self.token[:8]}... user={self.userId}>"
