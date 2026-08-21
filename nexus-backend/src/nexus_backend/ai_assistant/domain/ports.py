from collections.abc import AsyncIterator
from typing import Protocol

from nexus_backend.catalog.domain.entities import Product


class EmbeddingPort(Protocol):
    async def embed_text(self, text: str) -> list[float]: ...


class LLMPort(Protocol):
    async def generate_stream(
        self, system_prompt: str, user_message: str,
    ) -> AsyncIterator[str]: ...


class VectorStorePort(Protocol):
    async def similarity_search(
        self, embedding: list[float], top_k: int = 5,
    ) -> list[Product]: ...
