import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4

from nexus_backend.cart.application.services import CartService
from nexus_backend.cart.domain.entities import Cart
from nexus_backend.cart.presentation.router import _get_cart_service
from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.main import app


@pytest.fixture
def mock_cart_service() -> AsyncMock:
    return AsyncMock(spec=CartService)


@pytest.fixture(autouse=True)
def override_dependencies(mock_cart_service: AsyncMock, dummy_user: User):
    app.dependency_overrides[_get_cart_service] = lambda: mock_cart_service
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_cart_endpoint(async_client: AsyncClient, mock_cart_service: AsyncMock, dummy_cart: Cart, dummy_user: User):
    # Arrange
    mock_cart_service.get_cart.return_value = dummy_cart

    # Act
    response = await async_client.get("/api/v1/cart")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(dummy_cart.id)
    mock_cart_service.get_cart.assert_called_once_with(dummy_user.id)


@pytest.mark.asyncio
async def test_add_item_endpoint(async_client: AsyncClient, mock_cart_service: AsyncMock, dummy_cart: Cart, dummy_user: User):
    # Arrange
    mock_cart_service.add_item.return_value = dummy_cart
    pid = uuid4()
    payload = {"product_id": str(pid), "quantity": 2}

    # Act
    response = await async_client.post("/api/v1/cart/items", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(dummy_cart.id)
    mock_cart_service.add_item.assert_called_once_with(user_id=dummy_user.id, product_id=pid, quantity=2)


@pytest.mark.asyncio
async def test_update_item_endpoint(async_client: AsyncClient, mock_cart_service: AsyncMock, dummy_cart: Cart, dummy_user: User):
    # Arrange
    mock_cart_service.update_item_quantity.return_value = dummy_cart
    item_id = uuid4()
    payload = {"quantity": 5}

    # Act
    response = await async_client.put(f"/api/v1/cart/items/{item_id}", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(dummy_cart.id)
    mock_cart_service.update_item_quantity.assert_called_once_with(user_id=dummy_user.id, item_id=item_id, quantity=5)


@pytest.mark.asyncio
async def test_remove_item_endpoint(async_client: AsyncClient, mock_cart_service: AsyncMock, dummy_cart: Cart, dummy_user: User):
    # Arrange
    mock_cart_service.remove_item.return_value = dummy_cart
    item_id = uuid4()

    # Act
    response = await async_client.delete(f"/api/v1/cart/items/{item_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(dummy_cart.id)
    mock_cart_service.remove_item.assert_called_once_with(user_id=dummy_user.id, item_id=item_id)


@pytest.mark.asyncio
async def test_checkout_endpoint(async_client: AsyncClient, mock_cart_service: AsyncMock, dummy_cart: Cart, dummy_user: User):
    # Arrange
    mock_cart_service.checkout.return_value = dummy_cart

    # Act
    response = await async_client.post("/api/v1/cart/checkout")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(dummy_cart.id)
    mock_cart_service.checkout.assert_called_once_with(user_id=dummy_user.id)
