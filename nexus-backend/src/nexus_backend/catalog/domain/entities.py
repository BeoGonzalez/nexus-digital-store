import uuid
from dataclasses import dataclass, field
from datetime import datetime

from nexus_backend.shared.domain.entities import BaseEntity


@dataclass
class Genre(BaseEntity):
    name: str = ""


@dataclass
class VideoGame(BaseEntity):
    title: str = ""
    description: str = ""
    price_clp: int = 0
    stock: int = 0
    genres: list[Genre] = field(default_factory=list)
    embedding: list[float] = field(default_factory=list)
