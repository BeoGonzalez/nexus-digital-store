from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class User:
    """Entidad de dominio User mapeada desde AWS Cognito."""

    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    email: str = ""
    role: str = "user"  # 'admin', 'user', 'customer'
    banned: bool = False
    email_verified: bool = False
    image: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_admin(self) -> bool:
        """Determina si el usuario tiene privilegios administrativos."""
        return (self.role or "").strip().lower() == "admin"

    @property
    def is_active(self) -> bool:
        """Determina si la cuenta está activa (no baneada)."""
        return not self.banned
