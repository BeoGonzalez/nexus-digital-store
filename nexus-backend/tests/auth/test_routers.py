"""Pruebas de integración HTTP para los routers de autenticación (/api/v1/auth)."""

import pytest
from httpx import AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.main import app


class TestAuthRouterEndpoints:
    """Suite de integración HTTP para los endpoints de Auth."""

    @pytest.mark.asyncio
    async def test_auth_info_returns_neon_auth_url(self, async_client: AsyncClient) -> None:
        # Act
        response = await async_client.get("/api/v1/auth/info")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "neon_auth_url" in data
        assert "neonauth" in data["neon_auth_url"]
        assert "message" in data

    @pytest.mark.asyncio
    async def test_get_me_authenticated_user_returns_profile_dto(
        self, async_client: AsyncClient, dummy_user: User
    ) -> None:
        # Arrange
        app.dependency_overrides[get_current_user] = lambda: dummy_user

        try:
            # Act
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer mock_token"},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(dummy_user.id)
            assert data["name"] == dummy_user.name
            assert data["email"] == dummy_user.email
            assert data["role"] == "user"
            assert data["is_admin"] is False
            assert data["is_active"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_me_admin_user_returns_admin_flag(
        self, async_client: AsyncClient, dummy_admin: User
    ) -> None:
        # Arrange
        app.dependency_overrides[get_current_user] = lambda: dummy_admin

        try:
            # Act
            response = await async_client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer admin_token"},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == str(dummy_admin.id)
            assert data["role"] == "admin"
            assert data["is_admin"] is True
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_me_without_authorization_header_rejected_with_401(
        self, async_client: AsyncClient
    ) -> None:
        # Act - Sin dependency override, ejecutando el flujo real del middleware de seguridad
        response = await async_client.get("/api/v1/auth/me")

        # Assert
        # Regla de seguridad: Peticiones sin Bearer token deben ser rechazadas con 401 inmediatamente
        assert response.status_code == 401
