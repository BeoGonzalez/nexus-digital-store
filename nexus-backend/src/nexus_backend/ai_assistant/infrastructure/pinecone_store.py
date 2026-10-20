import asyncio
import logging
from uuid import UUID, uuid4

from pinecone import Pinecone

from nexus_backend.ai_assistant.domain.ports import VectorStorePort
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class PineconeVectorStoreAdapter(VectorStorePort):
    def __init__(
        self,
        api_key: str | None = None,
        index_name: str | None = None,
        namespace: str | None = None,
        fallback_store: VectorStorePort | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.PINECONE_API_KEY
        self._index_name = index_name or settings.PINECONE_INDEX_NAME
        self._namespace = namespace or settings.PINECONE_NAMESPACE
        self._fallback = fallback_store

        self._index = None
        if self._api_key and self._api_key != "your-pinecone-api-key":
            try:
                pc = Pinecone(api_key=self._api_key)
                self._index = pc.Index(self._index_name)
                logger.info("Connected to Pinecone index: %s", self._index_name)
            except Exception as e:
                logger.warning("Could not connect to Pinecone index '%s': %s", self._index_name, e)
                self._index = None

    def _match_to_entity(self, match: dict) -> VideoGame:
        metadata = match.get("metadata", {}) or {}
        raw_id = match.get("id") or metadata.get("id")
        try:
            game_id = UUID(str(raw_id)) if raw_id else uuid4()
        except (ValueError, TypeError):
            game_id = uuid4()

        genres_raw = metadata.get("genres", "")
        genres: list[Genre] = []
        if isinstance(genres_raw, list):
            genres = [Genre(name=str(g)) for g in genres_raw]
        elif isinstance(genres_raw, str) and genres_raw:
            genres = [Genre(name=g.strip()) for g in genres_raw.split(",") if g.strip()]

        return VideoGame(
            id=game_id,
            title=metadata.get("title", ""),
            description=metadata.get("description", ""),
            price_clp=int(metadata.get("price_clp", 0)),
            stock=int(metadata.get("stock", 0)),
            image_url=metadata.get("image_url"),
            genres=genres,
        )

    async def similarity_search(
        self, embedding: list[float], top_k: int = 5,
    ) -> list[VideoGame]:
        if not self._index:
            if self._fallback:
                logger.debug("Pinecone not configured or unavailable; delegating to fallback vector store.")
                return await self._fallback.similarity_search(embedding, top_k)
            return []

        def _query_pinecone() -> list[VideoGame]:
            try:
                kwargs = {
                    "vector": embedding,
                    "top_k": top_k,
                    "include_metadata": True,
                }
                if self._namespace:
                    kwargs["namespace"] = self._namespace

                response = self._index.query(**kwargs)
                matches = response.get("matches", [])
                return [self._match_to_entity(m) for m in matches]
            except Exception as exc:
                logger.error("Error querying Pinecone index '%s': %s", self._index_name, exc)
                return []

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, _query_pinecone)

        if not results and self._fallback:
            logger.debug("Pinecone returned no results or failed; falling back to secondary store.")
            return await self._fallback.similarity_search(embedding, top_k)

        return results

    async def upsert_game(
        self, video_game: VideoGame, embedding: list[float]
    ) -> None:
        if not self._index:
            return

        def _upsert() -> None:
            genres_str = ", ".join(g.name for g in video_game.genres)
            metadata = {
                "id": str(video_game.id),
                "title": video_game.title,
                "description": video_game.description,
                "price_clp": video_game.price_clp,
                "stock": video_game.stock,
                "genres": genres_str,
                "image_url": video_game.image_url or "",
            }
            vector_record = {
                "id": str(video_game.id),
                "values": embedding,
                "metadata": metadata,
            }
            kwargs = {"vectors": [vector_record]}
            if self._namespace:
                kwargs["namespace"] = self._namespace
            self._index.upsert(**kwargs)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _upsert)

