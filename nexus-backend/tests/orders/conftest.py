from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.orders.domain.entities import Order, OrderItem, OrderStatus
from nexus_backend.orders.domain.ports import OrderRepository
from nexus_backend.main import app


@pytest.fixture
def dummy_customer_user() -> User:
    return User(
        id="33333333-3333-3333-3333-333333333333",
        name="Nexus Customer",
        email="customer@nexus.cl",
        role="user",
        banned=False,
    )


@pytest.fixture
def mock_video_game_repo() -> AsyncMock:
    return AsyncMock(spec=VideoGameRepository)


@pytest.fixture
def mock_order_repo() -> AsyncMock:
    return AsyncMock(spec=OrderRepository)


@pytest.fixture
def dummy_video_game() -> VideoGame:
    return VideoGame(
        id=UUID("44444444-4444-4444-4444-444444444444"),
        title="Cyberpunk 2077",
        description="Open-world futuristic RPG",
        price_clp=30000,
        stock=10,
        genres=[Genre(id=uuid4(), name="RPG")],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def dummy_order(dummy_customer_user: User, dummy_video_game: VideoGame) -> Order:
    item = OrderItem(
        id=UUID("55555555-5555-5555-5555-555555555555"),
        video_game_id=dummy_video_game.id,
        quantity=2,
        unit_price_clp=30000,
        video_game=dummy_video_game,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return Order(
        id=UUID("66666666-6666-6666-6666-666666666666"),
        user_id=dummy_customer_user.id,
        total_amount_clp=60000,
        status=OrderStatus.CONFIRMED,
        items=[item],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def override_authenticated_customer(dummy_customer_user: User) -> User:
    app.dependency_overrides[get_current_user] = lambda: dummy_customer_user
    yield dummy_customer_user
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
