import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from nexus_backend.auth.application.services import AuthService
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.auth.presentation.router import _get_auth_service
from nexus_backend.main import app
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException, UnauthorizedException


@pytest.fixture
def mock_auth_service() -> AsyncMock:
    return AsyncMock(spec=AuthService)


@pytest.fixture(autouse=True)
def override_dependencies(mock_auth_service: AsyncMock, dummy_user: User):
    app.dependency_overrides[_get_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_endpoint_success(async_client: AsyncClient, mock_auth_service: AsyncMock, dummy_user: User):
    # Arrange
    mock_auth_service.register.return_value = dummy_user
    payload = {
        "email": dummy_user.email,
        "password": "password123",
        "full_name": dummy_user.full_name,
    }

    # Act
    response = await async_client.post("/api/v1/auth/register", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == dummy_user.email
    assert data["full_name"] == dummy_user.full_name
    mock_auth_service.register.assert_called_once_with(
        email=dummy_user.email, password="password123", full_name=dummy_user.full_name
    )


@pytest.mark.asyncio
async def test_register_endpoint_conflict(async_client: AsyncClient, mock_auth_service: AsyncMock):
    # Arrange
    mock_auth_service.register.side_effect = BusinessRuleViolationException("Email already registered")
    payload = {
        "email": "test@nexus.com",
        "password": "password123",
        "full_name": "Test User",
    }

    # Act
    response = await async_client.post("/api/v1/auth/register", json=payload)

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_endpoint_success(async_client: AsyncClient, mock_auth_service: AsyncMock):
    # Arrange
    mock_auth_service.authenticate.return_value = "mocked.jwt.token"
    payload = {
        "email": "test@nexus.com",
        "password": "password123",
    }

    # Act
    response = await async_client.post("/api/v1/auth/login", json=payload)

    # Assert
    assert response.status_code == 200
    assert response.json()["access_token"] == "mocked.jwt.token"
    assert response.json()["token_type"] == "bearer"
    mock_auth_service.authenticate.assert_called_once_with(email="test@nexus.com", password="password123")


@pytest.mark.asyncio
async def test_login_endpoint_unauthorized(async_client: AsyncClient, mock_auth_service: AsyncMock):
    # Arrange
    mock_auth_service.authenticate.side_effect = UnauthorizedException("Invalid credentials")
    payload = {
        "email": "test@nexus.com",
        "password": "wrongpassword",
    }

    # Act
    response = await async_client.post("/api/v1/auth/login", json=payload)

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_get_me_endpoint_success(async_client: AsyncClient, dummy_user: User):
    # Act
    # get_current_user dependency is overridden to return dummy_user
    response = await async_client.get("/api/v1/auth/me")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == dummy_user.email
    assert data["full_name"] == dummy_user.full_name
