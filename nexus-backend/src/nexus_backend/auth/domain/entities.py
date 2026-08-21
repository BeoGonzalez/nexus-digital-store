from dataclasses import dataclass

from nexus_backend.shared.domain.entities import BaseEntity


@dataclass
class User(BaseEntity):
    email: str = ""
    hashed_password: str = ""
    full_name: str = ""
    is_active: bool = True
