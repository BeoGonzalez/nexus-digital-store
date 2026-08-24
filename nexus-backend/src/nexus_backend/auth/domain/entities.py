from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from nexus_backend.shared.domain.entities import BaseEntity


@dataclass
class User(BaseEntity):
    """Entidad de dominio User mapeada desde Neon Auth (única fuente de verdad)."""

    name: str = ""
    email: str = ""
    role: str = "user"  # 'admin', 'user', 'customer'
    banned: bool = False
    email_verified: bool = False
    image: str | None = None

    @property
    def is_admin(self) -> bool:
        """Determina si el usuario tiene privilegios administrativos."""
        return (self.role or "").strip().lower() == "admin"

    @property
    def is_active(self) -> bool:
        """Determina si la cuenta está activa (no baneada)."""
        return not self.banned
