"""Pruebas unitarias para adaptadores de infraestructura del Asistente IA (VectorStore)."""

from unittest.mock import AsyncMock, patch
import pytest

from nexus_backend.ai_assistant.infrastructure.vector_store import PgVectorStoreAdapter
from nexus_backend.catalog.domain.entities import VideoGame


class TestVectorStoreAdapter:
    """Suite de validación para el adaptador PgVectorStoreAdapter."""

    @pytest.mark.asyncio
    async def test_similarity_search_delegates_to_videogame_repository(
        self, dummy_video_game: VideoGame
    ) -> None:
        # Arrange
        mock_session = AsyncMock()
        adapter = PgVectorStoreAdapter(mock_session)

        test_embedding = [0.42] * 384
        top_k_val = 7

        with patch.object(
            adapter._repo, "search_by_vector", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = [dummy_video_game]

            # Act
            results = await adapter.similarity_search(test_embedding, top_k=top_k_val)

            # Assert - Spying y verificación de contrato
            mock_search.assert_called_once_with(test_embedding, top_k_val)
            assert results == [dummy_video_game]
