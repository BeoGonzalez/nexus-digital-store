from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.domain.ports import EmbeddingPort, LLMPort, VectorStorePort
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.main import app


@pytest.fixture
def mock_embedding_port() -> AsyncMock:
    port = AsyncMock(spec=EmbeddingPort)
    port.embed_text.return_value = [0.1] * 384
    return port


@pytest.fixture
def mock_llm_port() -> MagicMock:
    port = MagicMock()

    async def fake_stream(system_prompt: str, user_message: str):
        yield "Recomiendo "
        yield "Elden "
        yield "Ring."

    port.generate_stream = MagicMock(side_effect=fake_stream)
    return port


@pytest.fixture
def mock_vector_store_port() -> AsyncMock:
    return AsyncMock(spec=VectorStorePort)


@pytest.fixture
def dummy_video_game() -> VideoGame:
    return VideoGame(
        id=UUID("77777777-7777-7777-7777-777777777777"),
        title="Elden Ring",
        description="Epic dark fantasy action RPG",
        price_clp=39990,
        stock=15,
        genres=[Genre(id=UUID("88888888-8888-8888-8888-888888888888"), name="Soulslike")],
        embedding=[0.1] * 384,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def assistant_service(
    mock_embedding_port: AsyncMock,
    mock_llm_port: MagicMock,
    mock_vector_store_port: AsyncMock,
) -> AssistantService:
    return AssistantService(
        embedding_port=mock_embedding_port,
        llm_port=mock_llm_port,
        vector_store_port=mock_vector_store_port,
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def mock_assistant_service() -> MagicMock:
    service = MagicMock(spec=AssistantService)

    async def fake_chat_stream(
        query: str,
        chat_history=None,
        session_id: str = "default-session",
    ):
        yield 'data: {"type": "products", "data": []}\n\n'
        yield 'data: {"type": "token", "data": "Hola"}\n\n'
        yield 'data: {"type": "done"}\n\n'

    service.chat_stream.side_effect = fake_chat_stream
    return service
