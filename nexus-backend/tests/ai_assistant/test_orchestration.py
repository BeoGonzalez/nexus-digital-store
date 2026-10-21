"""Pruebas unitarias para la orquestación (LCEL, LangGraph y CrewAI)."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from nexus_backend.ai_assistant.application.chains import (
    NEXUSBOT_SYSTEM_PROMPT,
    build_lcel_generation_chain,
    build_nexusbot_prompt,
)
from nexus_backend.ai_assistant.application.crew import run_nexus_crew
from nexus_backend.ai_assistant.application.graph import build_rag_graph
from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.config import get_settings


class TestOrchestrationPipeline:
    def test_lcel_prompt_construction(self) -> None:
        prompt = build_nexusbot_prompt()
        assert prompt is not None
        formatted = prompt.format_messages(
            context="1. Elden Ring - $39990 CLP",
            external_context="Ganador GOTY 2022",
            crew_analysis="Opción principal recomendada",
            messages=[],
            query="¿Qué juego me recomiendas?",
        )
        assert len(formatted) >= 2
        assert "NexusBot" in formatted[0].content
        assert formatted[-1].content == "¿Qué juego me recomiendas?"

    @pytest.mark.asyncio
    async def test_crew_ai_fallback_in_test_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(get_settings(), "GROQ_API_KEY", "")
        result = await run_nexus_crew(
            query="¿Tienen juegos de rol?",
            catalog_context="1. Cyberpunk 2077 - $35000 CLP",
            external_context="Ambientado en Night City",
            llm=None,
        )
        assert result is not None
        assert "Análisis" in result or "Stock" in result

    @pytest.mark.asyncio
    async def test_langgraph_three_nodes_pipeline(
        self,
        dummy_video_game: VideoGame,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(get_settings(), "GROQ_API_KEY", "")
        mock_embedding = AsyncMock()
        mock_embedding.embed_text.return_value = [0.1] * 384

        mock_vector_store = AsyncMock()
        mock_vector_store.similarity_search.return_value = [dummy_video_game]

        mock_wiki = AsyncMock()
        mock_wiki.fetch_trivia.return_value = "Gran juego de FromSoftware."

        mock_llm = MagicMock()

        async def fake_stream(system_prompt: str, user_message: str):
            yield "Recomiendo "
            yield "Elden Ring."

        mock_llm.generate_stream = MagicMock(side_effect=fake_stream)

        graph = build_rag_graph(
            embedding_port=mock_embedding,
            llm_port=mock_llm,
            vector_store_port=mock_vector_store,
            external_knowledge_port=mock_wiki,
        ).compile()

        state = {
            "query": "¿Tienen juegos difíciles?",
            "chat_history": [],
        }

        output = await graph.ainvoke(state)

        assert "response" in output
        assert "Elden Ring" in output["response"]
        assert len(output.get("retrieved_products", [])) == 1
        assert "Gran juego de FromSoftware" in output.get("external_context", "")
