from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user, require_admin
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.main import app


@pytest.fixture
def dummy_genre() -> Genre:
    return Genre(id=UUID("11111111-1111-1111-1111-111111111111"), name="RPG")


@pytest.fixture
def dummy_video_game(dummy_genre: Genre) -> VideoGame:
    return VideoGame(
        id=UUID("22222222-2222-2222-2222-222222222222"),
        title="Elden Ring",
        description="Epic fantasy action RPG",
        price_clp=49990,
        stock=25,
        genres=[dummy_genre],
        embedding=[0.1] * 384,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_video_game_repo() -> AsyncMock:
    return AsyncMock(spec=VideoGameRepository)


@pytest.fixture
def override_admin_user() -> User:
    admin = User(
        id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        name="Admin Chief",
        email="admin@nexus.cl",
        role="admin",
        banned=False,
    )
    app.dependency_overrides[require_admin] = lambda: admin
    app.dependency_overrides[get_current_user] = lambda: admin
    yield admin
    app.dependency_overrides.pop(require_admin, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
