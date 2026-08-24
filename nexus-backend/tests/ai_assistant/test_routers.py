"""Pruebas de integración HTTP para los routers del Asistente IA (/api/v1/assistant)."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock
import pytest
from httpx import AsyncClient

from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.presentation.router import _get_assistant_service
from nexus_backend.main import app


@pytest.fixture
def mock_assistant_service() -> MagicMock:
    service = MagicMock(spec=AssistantService)

    async def fake_chat_stream(query: str, chat_history=None) -> AsyncIterator[str]:
        yield 'data: {"type": "products", "data": []}\n\n'
        yield 'data: {"type": "token", "data": "Hola"}\n\n'
        yield 'data: {"type": "done"}\n\n'

    service.chat_stream.side_effect = fake_chat_stream
    return service


@pytest.fixture(autouse=True)
def override_assistant_dependencies(mock_assistant_service: MagicMock):
    app.dependency_overrides[_get_assistant_service] = lambda: mock_assistant_service
    yield
    app.dependency_overrides.pop(_get_assistant_service, None)


class TestAssistantRouterEndpoints:
    """Suite de integración HTTP para los endpoints del Asistente IA."""

    @pytest.mark.asyncio
    async def test_chat_stream_endpoint_returns_streaming_response_200(
        self,
        async_client: AsyncClient,
        mock_assistant_service: MagicMock,
    ) -> None:
        # Arrange
        payload = {
            "query": "¿Qué juegos me recomiendas?",
            "chat_history": [{"role": "user", "content": "Hola"}],
        }

        # Act
        response = await async_client.post("/api/v1/assistant/chat", json=payload)

        # Assert
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers.get("cache-control") == "no-cache"

        # Validar el contenido del stream SSE consumido
        content = response.text
        assert "data: " in content
        assert '"type": "products"' in content
        assert '"type": "token"' in content
        assert '"type": "done"' in content

    @pytest.mark.asyncio
    async def test_chat_stream_endpoint_validation_error_empty_query_returns_422(
        self,
        async_client: AsyncClient,
    ) -> None:
        # Arrange: query vacía viola el min_length=1 de ChatRequest
        invalid_payload = {"query": ""}

        # Act
        response = await async_client.post("/api/v1/assistant/chat", json=invalid_payload)

        # Assert
        assert response.status_code == 422
