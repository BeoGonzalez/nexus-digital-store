"""Pruebas de integración HTTP para los routers de autenticación (/api/v1/auth)."""

import pytest
from httpx import AsyncClient

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user
from nexus_backend.main import app


class TestAuthRouterEndpoints:
    """Suite de integración HTTP para los endpoints de Auth."""

    @pytest.mark.asyncio
    async def test_auth_info_returns_cognito_config(self, async_client: AsyncClient) -> None:
        # Act
        response = await async_client.get("/api/v1/auth/info")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["auth_provider"] == "Amazon Cognito"
        assert "cognito_region" in data
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

    @pytest.mark.asyncio
    async def test_login_delegates_to_cognito_and_returns_token(
        self, async_client: AsyncClient
    ) -> None:
        from unittest.mock import AsyncMock
        from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier, get_cognito_verifier

        mock_verifier = AsyncMock(spec=CognitoTokenVerifier)
        mock_verifier.authenticate_user.return_value = "mock_cognito_id_token_xyz"

        app.dependency_overrides[get_cognito_verifier] = lambda: mock_verifier

        try:
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"email": "player@nexus.cl", "password": "SecurePassword123!"},
            )
            assert response.status_code == 200
            assert response.json()["token"] == "mock_cognito_id_token_xyz"
            mock_verifier.authenticate_user.assert_called_once_with("player@nexus.cl", "SecurePassword123!")
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_delegates_to_cognito_and_returns_created_user(
        self, async_client: AsyncClient
    ) -> None:
        from unittest.mock import AsyncMock
        from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier, get_cognito_verifier

        mock_verifier = AsyncMock(spec=CognitoTokenVerifier)
        mock_verifier.register_user.return_value = {"UserSub": "sub-12345-abcde"}

        app.dependency_overrides[get_cognito_verifier] = lambda: mock_verifier

        try:
            response = await async_client.post(
                "/api/v1/auth/register",
                json={"name": "New Player", "email": "new@nexus.cl", "password": "SecurePassword123!"},
            )
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "sub-12345-abcde"
            assert data["email"] == "new@nexus.cl"
            assert data["name"] == "New Player"
            mock_verifier.register_user.assert_called_once_with("new@nexus.cl", "SecurePassword123!", "New Player")
        finally:
            app.dependency_overrides.clear()
