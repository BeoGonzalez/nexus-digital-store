"""Pruebas unitarias para PineconeVectorStoreAdapter y WikipediaAdapter."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID
import pytest

from nexus_backend.ai_assistant.infrastructure.pinecone_store import PineconeVectorStoreAdapter
from nexus_backend.ai_assistant.infrastructure.wikipedia import WikipediaAdapter
from nexus_backend.catalog.domain.entities import VideoGame


class TestPineconeVectorStoreAdapter:
    @pytest.mark.asyncio
    async def test_pinecone_query_maps_matches_to_videogame_entities(self) -> None:
        adapter = PineconeVectorStoreAdapter(
            api_key="test-key",
            index_name="test-index",
            namespace="nexus_chile",
        )

        mock_index = MagicMock()
        mock_index.query.return_value = {
            "matches": [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "score": 0.95,
                    "metadata": {
                        "title": "Cyberpunk 2077",
                        "description": "RPG futurista en Night City",
                        "price_clp": 35000,
                        "stock": 10,
                        "genres": "RPG, Acción",
                    },
                }
            ]
        }
        adapter._index = mock_index

        results = await adapter.similarity_search([0.1] * 384, top_k=1)

        assert len(results) == 1
        game = results[0]
        assert game.id == UUID("11111111-1111-1111-1111-111111111111")
        assert game.title == "Cyberpunk 2077"
        assert game.price_clp == 35000
        assert game.stock == 10
        assert len(game.genres) == 2
        assert game.genres[0].name == "RPG"
        assert game.genres[1].name == "Acción"

    @pytest.mark.asyncio
    async def test_pinecone_fallback_when_unconfigured(
        self, dummy_video_game: VideoGame
    ) -> None:
        mock_fallback = AsyncMock()
        mock_fallback.similarity_search.return_value = [dummy_video_game]

        adapter = PineconeVectorStoreAdapter(
            api_key="",  # sin key
            fallback_store=mock_fallback,
        )

        results = await adapter.similarity_search([0.2] * 384, top_k=3)

        assert results == [dummy_video_game]
        mock_fallback.similarity_search.assert_called_once_with([0.2] * 384, 3)

    @pytest.mark.asyncio
    async def test_upsert_game_calls_pinecone_upsert(
        self, dummy_video_game: VideoGame
    ) -> None:
        adapter = PineconeVectorStoreAdapter(
            api_key="test-key",
            index_name="test-index",
            namespace="nexus_chile",
        )
        mock_index = MagicMock()
        adapter._index = mock_index

        await adapter.upsert_game(dummy_video_game, [0.3] * 384)

        mock_index.upsert.assert_called_once()
        call_kwargs = mock_index.upsert.call_args[1]
        assert call_kwargs["namespace"] == "nexus_chile"
        assert len(call_kwargs["vectors"]) == 1
        record = call_kwargs["vectors"][0]
        assert record["id"] == str(dummy_video_game.id)
        assert record["metadata"]["title"] == dummy_video_game.title


class TestWikipediaAdapter:
    @pytest.mark.asyncio
    async def test_fetch_trivia_returns_trimmed_text(self) -> None:
        adapter = WikipediaAdapter(lang="es")
        mock_wrapper = MagicMock()
        mock_wrapper.run.return_value = "Elden Ring ganó el premio al Juego del Año en 2022."
        adapter._wiki = mock_wrapper

        trivia = await adapter.fetch_trivia("Elden Ring")

        assert "Juego del Año" in trivia
        mock_wrapper.run.assert_called_once_with("Elden Ring videojuego")

    @pytest.mark.asyncio
    async def test_fetch_trivia_handles_exceptions_gracefully(self) -> None:
        adapter = WikipediaAdapter(lang="es")
        mock_wrapper = MagicMock()
        mock_wrapper.run.side_effect = Exception("Wikipedia timeout")
        adapter._wiki = mock_wrapper

        trivia = await adapter.fetch_trivia("Unknown Game")

        assert trivia == "Sin datos externos."

