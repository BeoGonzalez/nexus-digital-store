"""Pruebas de integración HTTP para los routers de catálogo (/api/v1/video-games)."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4
import pytest
from httpx import AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user, require_admin
from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.catalog.presentation.router import _get_catalog_service
from nexus_backend.main import app
from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException, ResourceNotFoundException


@pytest.fixture
def mock_catalog_service() -> AsyncMock:
    return AsyncMock(spec=CatalogService)


@pytest.fixture(autouse=True)
def override_catalog_dependencies(mock_catalog_service: AsyncMock):
    app.dependency_overrides[_get_catalog_service] = lambda: mock_catalog_service
    yield
    app.dependency_overrides.pop(_get_catalog_service, None)


class TestCatalogRouterEndpoints:
    """Suite de integración HTTP para los endpoints públicos y protegidos del catálogo."""

    @pytest.mark.asyncio
    async def test_list_video_games_public_endpoint_returns_200(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_catalog_service.list_video_games.return_value = [dummy_video_game]

        # Act - Petición pública sin headers de autenticación
        response = await async_client.get("/api/v1/video-games?skip=0&limit=50")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(dummy_video_game.id)
        assert data[0]["title"] == dummy_video_game.title
        assert data[0]["price_clp"] == dummy_video_game.price_clp
        mock_catalog_service.list_video_games.assert_called_once_with(skip=0, limit=50)

    @pytest.mark.asyncio
    async def test_get_video_game_detail_returns_200(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_catalog_service.get_video_game.return_value = dummy_video_game

        # Act
        response = await async_client.get(f"/api/v1/video-games/{dummy_video_game.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(dummy_video_game.id)
        assert data["title"] == dummy_video_game.title
        mock_catalog_service.get_video_game.assert_called_once_with(dummy_video_game.id)

    @pytest.mark.asyncio
    async def test_get_video_game_not_found_returns_404(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
    ) -> None:
        # Arrange
        missing_id = uuid4()
        mock_catalog_service.get_video_game.side_effect = ResourceNotFoundException(
            f"Video game with ID {missing_id} not found"
        )

        # Act
        response = await async_client.get(f"/api/v1/video-games/{missing_id}")

        # Assert
        # Regla de presentación: ResourceNotFoundException debe transformarse a HTTP 404
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_video_game_admin_authorized_returns_201(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
        override_admin_user: User,
    ) -> None:
        # Arrange
        mock_catalog_service.create_video_game.return_value = dummy_video_game
        payload = {
            "title": "Elden Ring",
            "description": "Epic fantasy action RPG",
            "price_clp": 49990,
            "stock": 25,
            "genre_names": ["RPG"],
        }

        # Act
        response = await async_client.post(
            "/api/v1/video-games",
            json=payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(dummy_video_game.id)
        assert data["title"] == "Elden Ring"
        assert data["price_clp"] == 49990
        assert mock_catalog_service.create_video_game.call_count == 1

    @pytest.mark.asyncio
    async def test_create_video_game_unauthenticated_rejected_with_401(
        self,
        async_client: AsyncClient,
    ) -> None:
        # Act - Petición sin token de autenticación
        response = await async_client.post(
            "/api/v1/video-games",
            json={"title": "Test", "description": "Desc", "price_clp": 1000, "stock": 1},
        )

        # Assert
        # Regla de seguridad: Petición sin Bearer token rechazada inmediatamente
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_video_game_validation_error_negative_price_rejected_with_422(
        self,
        async_client: AsyncClient,
        override_admin_user: User,
    ) -> None:
        # Arrange
        invalid_payload = {
            "title": "Invalid Game",
            "description": "Negative price test",
            "price_clp": -5000,  # Violación de validación (gt=0)
            "stock": 10,
        }

        # Act
        response = await async_client.post(
            "/api/v1/video-games",
            json=invalid_payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        # Assert
        # Regla de validación: Pydantic debe rechazar el payload inválido con 422
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_update_video_game_admin_authorized_returns_200(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
        override_admin_user: User,
    ) -> None:
        # Arrange
        dummy_video_game.price_clp = 39990
        mock_catalog_service.update_video_game.return_value = dummy_video_game
        update_payload = {"price_clp": 39990}

        # Act
        response = await async_client.put(
            f"/api/v1/video-games/{dummy_video_game.id}",
            json=update_payload,
            headers={"Authorization": "Bearer admin_token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["price_clp"] == 39990
        assert mock_catalog_service.update_video_game.call_count == 1

    @pytest.mark.asyncio
    async def test_delete_video_game_admin_authorized_returns_200(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
        override_admin_user: User,
    ) -> None:
        # Arrange
        mock_catalog_service.delete_video_game.return_value = True

        # Act
        response = await async_client.delete(
            f"/api/v1/video-games/{dummy_video_game.id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert str(dummy_video_game.id) in data["message"]
        mock_catalog_service.delete_video_game.assert_called_once_with(dummy_video_game.id)

    @pytest.mark.asyncio
    async def test_delete_video_game_referenced_in_orders_returns_409_conflict(
        self,
        async_client: AsyncClient,
        mock_catalog_service: AsyncMock,
        dummy_video_game: VideoGame,
        override_admin_user: User,
    ) -> None:
        # Arrange
        mock_catalog_service.delete_video_game.side_effect = BusinessRuleViolationException(
            f"Cannot delete video game {dummy_video_game.id} because it is referenced in existing customer orders."
        )

        # Act
        response = await async_client.delete(
            f"/api/v1/video-games/{dummy_video_game.id}",
            headers={"Authorization": "Bearer admin_token"},
        )

        # Assert
        # Regla de negocio: La violación de integridad referencial histórica devuelve HTTP 409 Conflict
        assert response.status_code == 409
        assert "referenced in existing customer orders" in response.json()["detail"]
