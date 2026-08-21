from dataclasses import dataclass, field
from typing import TypedDict

from nexus_backend.catalog.domain.entities import Product


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class AssistantState(TypedDict, total=False):
    query: str
    chat_history: list[ChatMessage]
    retrieved_products: list[Product]
    context: str
    response: str
