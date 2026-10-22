from collections.abc import AsyncIterator
from typing import Protocol

from nexus_backend.catalog.domain.entities import VideoGame


class EmbeddingPort(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...


class LLMPort(Protocol):
    async def generate(self, system_prompt: str, user_message: str) -> str: ...

    async def generate_stream(
        self, system_prompt: str, user_message: str,
    ) -> AsyncIterator[str]: ...


class VectorStorePort(Protocol):
    async def similarity_search(
        self, embedding: list[float], top_k: int = 5,
    ) -> list[VideoGame]: ...


class ExternalKnowledgePort(Protocol):
    async def fetch_trivia(self, topic: str) -> str: ...


class GamingNewsPort(Protocol):
    async def fetch_news(self, query: str) -> str: ...


class PriceComparisonPort(Protocol):
    async def compare_price(
        self, game_title: str, nexus_price_clp: int
    ) -> dict: ...


class DecisionEnginePort(Protocol):
    async def classify_intent(self, query: str) -> str: ...

    async def evaluate_decision(self, query: str) -> dict: ...


class EmailPort(Protocol):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        content_html: str,
        content_text: str = "",
    ) -> dict: ...
