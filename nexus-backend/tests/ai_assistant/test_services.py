"""Pruebas unitarias para AssistantService con validación RAG, contratos SSE y LangGraph."""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest

from nexus_backend.ai_assistant.application.graph import SYSTEM_PROMPT
from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.domain.entities import ChatMessage
from nexus_backend.catalog.domain.entities import VideoGame


class TestAssistantService:
    """Suite de validación para la orquestación RAG y streaming del Asistente IA."""

    @pytest.fixture(autouse=True)
    def mock_crew_orchestration(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_crew(*args, **kwargs):
            return "Análisis estratégico simulado de CrewAI para tests."

        monkeypatch.setattr(
            "nexus_backend.ai_assistant.application.services.run_nexus_crew",
            fake_crew,
        )
        monkeypatch.setattr(
            "nexus_backend.ai_assistant.application.graph.run_nexus_crew",
            fake_crew,
        )

    @pytest.mark.asyncio
    async def test_chat_stream_assembles_context_and_validates_contract(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        query = "¿Tienen juegos tipo Souls?"
        mock_vector = [0.123] * 384
        mock_embedding_port.embed_text.return_value = mock_vector
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]

        history = [
            ChatMessage(role="user", content="Hola"),
            ChatMessage(role="assistant", content="¡Hola! ¿Qué buscas?"),
        ]

        # Act
        chunks: list[str] = []
        async for chunk in assistant_service.chat_stream(query, history):
            chunks.append(chunk)

        # Assert - Spying y contratos de comunicación
        # 1. Contrato de embeddings y búsqueda vectorial
        mock_embedding_port.embed_text.assert_called_once_with(query)
        mock_vector_store_port.similarity_search.assert_called_once_with(mock_vector, top_k=5)

        # 2. Contrato con LLM (System Prompt y Ensamble de Contexto)
        llm_call_args = mock_llm_port.generate_stream.call_args
        assert llm_call_args is not None
        called_system_prompt, called_user_message = llm_call_args[0]

        assert called_system_prompt == SYSTEM_PROMPT
        assert dummy_video_game.title in called_user_message
        assert str(dummy_video_game.price_clp) in called_user_message
        assert "Soulslike" in called_user_message
        assert "¡Hola! ¿Qué buscas?" in called_user_message
        assert "¿Tienen juegos tipo Souls?" in called_user_message

        # 3. Protocolo SSE (Server-Sent Events)
        assert len(chunks) == 5  # 1 products, 3 token, 1 done
        assert chunks[0].startswith("data: ")

        first_chunk = json.loads(chunks[0].replace("data: ", ""))
        assert first_chunk["type"] == "products"
        assert len(first_chunk["data"]) == 1
        assert first_chunk["data"][0]["title"] == dummy_video_game.title
        assert first_chunk["data"][0]["price_clp"] == str(dummy_video_game.price_clp)

        # Tokens intermedios
        token_chunk_1 = json.loads(chunks[1].replace("data: ", ""))
        assert token_chunk_1["type"] == "token"
        assert token_chunk_1["data"] == "Recomiendo "

        # Chunk finalizador
        done_chunk = json.loads(chunks[4].replace("data: ", ""))
        assert done_chunk["type"] == "done"

    @pytest.mark.asyncio
    async def test_chat_stream_empty_results_and_history_fallback(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
    ) -> None:
        # Arrange
        mock_embedding_port.embed_text.return_value = [0.0] * 384
        mock_vector_store_port.similarity_search.return_value = []
        query = "Juegos de carreras espaciales que no existen"

        # Act
        chunks = []
        async for chunk in assistant_service.chat_stream(query, chat_history=None):
            chunks.append(chunk)

        # Assert
        _, called_user_message = mock_llm_port.generate_stream.call_args[0]
        assert "No se encontraron videojuegos relevantes" in called_user_message

        first_chunk = json.loads(chunks[0].replace("data: ", ""))
        assert first_chunk["type"] == "products"
        assert first_chunk["data"] == []

    @pytest.mark.asyncio
    async def test_chat_stream_truncates_history_to_last_six_messages(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange - Historial extenso de 10 mensajes
        long_history = [
            ChatMessage(role="user", content=f"Message {i}")
            for i in range(10)
        ]
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]

        # Act
        _ = [chunk async for chunk in assistant_service.chat_stream("Query", long_history)]

        # Assert
        _, called_user_message = mock_llm_port.generate_stream.call_args[0]
        # Regla de contexto: Solo los últimos 6 mensajes deben incluirse para evitar desbordar la ventana de contexto
        assert "Message 0" not in called_user_message
        assert "Message 1" not in called_user_message
        assert "Message 2" not in called_user_message
        assert "Message 3" not in called_user_message
        assert "Message 4" in called_user_message
        assert "Message 9" in called_user_message

    @pytest.mark.asyncio
    async def test_chat_synchronous_rag_graph_execution(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_embedding_port.embed_text.return_value = [0.1] * 384
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]

        # Act - Ejecuta el StateGraph compilado de LangGraph
        response = await assistant_service.chat("¿Cuál es el juego más recomendado?")

        # Assert
        assert response == "Recomiendo Elden Ring."

    @pytest.mark.asyncio
    async def test_chat_stream_memory_saver_multi_turn_persistence(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_embedding_port.embed_text.return_value = [0.1] * 384
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]
        session_id = "user-session-42"

        # Turno 1: el usuario pregunta por Elden Ring
        _ = [
            chunk
            async for chunk in assistant_service.chat_stream(
                query="¿Tienen Elden Ring?",
                chat_history=None,
                session_id=session_id,
            )
        ]

        # Turno 2: el usuario pregunta por el precio sin reenviar chat_history
        _ = [
            chunk
            async for chunk in assistant_service.chat_stream(
                query="¿Cuánto vale?",
                chat_history=None,
                session_id=session_id,
            )
        ]

        # Assert - El LLM debe haber recibido en Turno 2 el historial recuperado de MemorySaver
        _, called_user_message = mock_llm_port.generate_stream.call_args[0]
        assert "user: ¿Tienen Elden Ring?" in called_user_message
        assert "assistant: Recomiendo Elden Ring." in called_user_message
        assert "Pregunta del cliente: ¿Cuánto vale?" in called_user_message

    @pytest.mark.asyncio
    async def test_chat_stream_memory_saver_session_isolation(
        self,
        assistant_service: AssistantService,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_embedding_port.embed_text.return_value = [0.1] * 384
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]

        # Sesión A habla de Dark Souls
        _ = [
            chunk
            async for chunk in assistant_service.chat_stream(
                query="Quiero Dark Souls",
                chat_history=None,
                session_id="session-user-A",
            )
        ]

        # Sesión B hace una pregunta independiente
        _ = [
            chunk
            async for chunk in assistant_service.chat_stream(
                query="Quiero Mario Kart",
                chat_history=None,
                session_id="session-user-B",
            )
        ]

        # Assert - La sesión B NO debe tener rastros de la conversación de la sesión A
        _, called_user_message = mock_llm_port.generate_stream.call_args[0]
        assert "Dark Souls" not in called_user_message
        assert "Quiero Mario Kart" in called_user_message
