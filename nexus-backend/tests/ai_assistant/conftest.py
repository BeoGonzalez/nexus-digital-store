import pytest
import pytest_asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from decimal import Decimal

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nexus_backend.ai_assistant.domain.ports import EmbeddingPort, LLMPort, VectorStorePort
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.main import app


@pytest.fixture
def mock_embedding_port() -> AsyncMock:
    return AsyncMock(spec=EmbeddingPort)


@pytest.fixture
def mock_llm_port() -> MagicMock:
    port = MagicMock()
    
    async def mock_generate_stream(system_prompt: str, user_message: str):
        yield "Hello"
        yield " "
        yield "World"
        
    port.generate_stream.side_effect = mock_generate_stream
    return port


@pytest.fixture
def mock_vector_store_port() -> AsyncMock:
    return AsyncMock(spec=VectorStorePort)


@pytest.fixture
def dummy_product() -> Product:
    return Product(
        id=uuid4(),
        name="RTX 4090",
        brand="NVIDIA",
        category="GPU",
        description="Flagship graphics card",
        price=Decimal("1599.99"),
        stock=10,
        specifications={"vram": "24GB"},
        image_url="http://example.com/rtx4090.png",
        embedding=[],
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
