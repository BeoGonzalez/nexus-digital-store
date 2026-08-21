import pytest
import pytest_asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.domain.ports import PasswordHasherPort, TokenIssuerPort, UserRepository
from nexus_backend.main import app

@pytest.fixture
def mock_user_repo() -> AsyncMock:
    repo = AsyncMock(spec=UserRepository)
    return repo


@pytest.fixture
def mock_password_hasher() -> MagicMock:
    hasher = MagicMock(spec=PasswordHasherPort)
    hasher.hash.return_value = "hashed_secret"
    hasher.verify.return_value = True
    return hasher


@pytest.fixture
def mock_token_issuer() -> MagicMock:
    issuer = MagicMock(spec=TokenIssuerPort)
    issuer.issue.return_value = "mocked.jwt.token"
    return issuer


@pytest.fixture
def dummy_user() -> User:
    return User(
        id=uuid4(),
        email="test@nexus.com",
        hashed_password="hashed_secret",
        full_name="Test User",
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        yield client
