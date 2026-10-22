from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock

from nexus_backend.auth.domain.entities import User
from nexus_backend.main import app


@pytest.fixture
def dummy_user() -> User:
    """Fixture de usuario estándar (cliente) no baneado."""
    return User(
        id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        name="John Gamer",
        email="john@nexus.cl",
        role="user",
        banned=False,
        email_verified=True,
        image=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def dummy_admin() -> User:
    """Fixture de usuario con rol administrativo."""
    return User(
        id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        name="Admin Boss",
        email="admin@nexus.cl",
        role="admin",
        banned=False,
        email_verified=True,
        image=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def dummy_banned_user() -> User:
    """Fixture de usuario con cuenta suspendida/baneada."""
    return User(
        id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        name="Banned Cheater",
        email="cheater@nexus.cl",
        role="user",
        banned=True,
        email_verified=True,
        image=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    """Cliente HTTP asíncrono para pruebas de integración sobre FastAPI."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        yield client
