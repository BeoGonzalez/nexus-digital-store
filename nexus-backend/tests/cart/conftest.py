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

from nexus_backend.cart.domain.entities import Cart, CartItem
from nexus_backend.cart.domain.ports import CartRepository
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.domain.ports import ProductRepository
from nexus_backend.auth.domain.entities import User
from nexus_backend.main import app

@pytest.fixture
def mock_cart_repo() -> AsyncMock:
    return AsyncMock(spec=CartRepository)

@pytest.fixture
def mock_product_repo() -> AsyncMock:
    return AsyncMock(spec=ProductRepository)

@pytest.fixture
def dummy_user() -> User:
    return User(
        id=uuid4(),
        email="test@nexus.com",
        hashed_password="hashed_secret",
        full_name="Test User",
    )

@pytest.fixture
def dummy_product() -> Product:
    return Product(
        id=uuid4(),
        name="RTX 4090",
        brand="NVIDIA",
        category="GPU",
        description="Flagship",
        price=Decimal("1599.99"),
        stock=10,
        specifications={},
        image_url="http://test.com/img.png",
        embedding=[],
    )

from nexus_backend.cart.domain.entities import Cart, CartItem, CartStatus

@pytest.fixture
def dummy_cart(dummy_user: User, dummy_product: Product) -> Cart:
    return Cart(
        id=uuid4(),
        user_id=dummy_user.id,
        status=CartStatus.ACTIVE,
        items=[
            CartItem(
                id=uuid4(),
                product_id=dummy_product.id,
                quantity=2,
                unit_price=Decimal("1599.99")
            )
        ]
    )

@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
