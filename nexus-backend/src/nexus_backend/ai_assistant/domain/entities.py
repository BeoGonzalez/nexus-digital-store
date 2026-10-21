from dataclasses import dataclass
from typing import TypedDict

from nexus_backend.catalog.domain.entities import VideoGame


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str


class AssistantState(TypedDict, total=False):
    query: str
    tenant_id: str
    intent: str
    decision_metrics: dict
    chat_history: list[ChatMessage]
    retrieved_products: list[VideoGame]
    context: str
    external_context: str
    crew_analysis: str
    response: str
