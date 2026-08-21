import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
import json

from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.presentation.router import _get_assistant_service
from nexus_backend.main import app


@pytest.fixture
def mock_assistant_service() -> AsyncMock:
    service = AsyncMock(spec=AssistantService)
    
    async def mock_chat_stream(query, chat_history):
        yield f"data: {json.dumps({'type': 'token', 'data': 'Hello'})}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    service.chat_stream = mock_chat_stream
    return service


@pytest.fixture(autouse=True)
def override_dependencies(mock_assistant_service: AsyncMock):
    app.dependency_overrides[_get_assistant_service] = lambda: mock_assistant_service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_chat_endpoint_stream(async_client: AsyncClient, mock_assistant_service: AsyncMock):
    # Arrange
    payload = {
        "query": "Hello",
        "chat_history": []
    }

    # Act
    lines = []
    async with async_client.stream("POST", "/api/v1/assistant/chat", json=payload) as response:
        assert response.status_code == 200
        async for line in response.aiter_lines():
            if line.strip():
                lines.append(line)

    # Assert
    assert len(lines) == 2
    assert "Hello" in lines[0]
    assert "done" in lines[1]
