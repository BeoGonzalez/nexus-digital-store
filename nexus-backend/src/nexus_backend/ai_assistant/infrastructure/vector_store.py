from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyVideoGameRepository


class PgVectorStoreAdapter:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = SQLAlchemyVideoGameRepository(session)

    async def similarity_search(
        self, embedding: list[float], top_k: int = 5,
    ) -> list[VideoGame]:
        return await self._repo.search_by_vector(embedding, top_k)
