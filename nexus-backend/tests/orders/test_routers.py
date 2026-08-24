"""Pruebas de integración HTTP para los routers de órdenes (/api/v1/orders)."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.orders.application.services import OrderService
from nexus_backend.orders.domain.entities import Order
from nexus_backend.orders.presentation.router import _get_order_service
from nexus_backend.main import app
from nexus_backend.shared.domain.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
)


@pytest.fixture
def mock_order_service() -> AsyncMock:
    return AsyncMock(spec=OrderService)


@pytest.fixture(autouse=True)
def override_order_dependencies(mock_order_service: AsyncMock):
    app.dependency_overrides[_get_order_service] = lambda: mock_order_service
    yield
    app.dependency_overrides.pop(_get_order_service, None)


class TestOrderRouterEndpoints:
    """Suite de integración HTTP para los endpoints de órdenes."""

    @pytest.mark.asyncio
    async def test_get_user_orders_authenticated_returns_200(
        self,
        async_client: AsyncClient,
        mock_order_service: AsyncMock,
        dummy_order: Order,
        override_authenticated_customer: User,
    ) -> None:
        # Arrange
        mock_order_service.get_user_orders.return_value = [dummy_order]

        # Act
        response = await async_client.get(
            "/api/v1/orders",
            headers={"Authorization": "Bearer valid_token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(dummy_order.id)
        assert data[0]["user_id"] == str(dummy_order.user_id)
        assert data[0]["total_amount_clp"] == dummy_order.total_amount_clp
        mock_order_service.get_user_orders.assert_called_once_with(override_authenticated_customer.id)

    @pytest.mark.asyncio
    async def test_get_user_orders_unauthenticated_rejected_with_401(
        self,
        async_client: AsyncClient,
    ) -> None:
        # Act - Petición sin token
        response = await async_client.get("/api/v1/orders")

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_order_authenticated_returns_201(
        self,
        async_client: AsyncClient,
        mock_order_service: AsyncMock,
        dummy_order: Order,
        override_authenticated_customer: User,
    ) -> None:
        # Arrange
        mock_order_service.create_order.return_value = dummy_order
        payload = {
            "items": [
                {"video_game_id": str(dummy_order.items[0].video_game_id), "quantity": 2}
            ]
        }

        # Act
        response = await async_client.post(
            "/api/v1/orders",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(dummy_order.id)
        assert data["total_amount_clp"] == dummy_order.total_amount_clp
        assert len(data["items"]) == 1
        assert mock_order_service.create_order.call_count == 1

    @pytest.mark.asyncio
    async def test_create_order_unauthenticated_rejected_with_401(
        self,
        async_client: AsyncClient,
    ) -> None:
        # Act
        response = await async_client.post(
            "/api/v1/orders",
            json={"items": [{"video_game_id": str(uuid4()), "quantity": 1}]},
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock_returns_409_conflict(
        self,
        async_client: AsyncClient,
        mock_order_service: AsyncMock,
        override_authenticated_customer: User,
    ) -> None:
        # Arrange
        mock_order_service.create_order.side_effect = BusinessRuleViolationException(
            "Not enough stock for video game 'Elden Ring'."
        )
        payload = {"items": [{"video_game_id": str(uuid4()), "quantity": 10}]}

        # Act
        response = await async_client.post(
            "/api/v1/orders",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        # Assert
        # Regla de presentación: BusinessRuleViolationException se transforma en HTTP 409 Conflict
        assert response.status_code == 409
        assert "Not enough stock" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_order_missing_game_returns_404_not_found(
        self,
        async_client: AsyncClient,
        mock_order_service: AsyncMock,
        override_authenticated_customer: User,
    ) -> None:
        # Arrange
        missing_id = uuid4()
        mock_order_service.create_order.side_effect = ResourceNotFoundException(
            f"Video game {missing_id} not found."
        )
        payload = {"items": [{"video_game_id": str(missing_id), "quantity": 1}]}

        # Act
        response = await async_client.post(
            "/api/v1/orders",
            json=payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        # Assert
        # Regla de presentación: ResourceNotFoundException se transforma en HTTP 404 Not Found
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_order_invalid_quantity_rejected_with_422(
        self,
        async_client: AsyncClient,
        override_authenticated_customer: User,
    ) -> None:
        # Arrange: quantity <= 0 viola la validación Pydantic (Field gt=0)
        invalid_payload = {"items": [{"video_game_id": str(uuid4()), "quantity": 0}]}

        # Act
        response = await async_client.post(
            "/api/v1/orders",
            json=invalid_payload,
            headers={"Authorization": "Bearer valid_token"},
        )

        # Assert
        assert response.status_code == 422
