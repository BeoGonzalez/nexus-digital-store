import pytest
import pytest_asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.domain.ports import ProductRepository
from nexus_backend.main import app


@pytest.fixture
def mock_product_repo() -> AsyncMock:
    return AsyncMock(spec=ProductRepository)


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
        embedding=[0.1] * 384,
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
