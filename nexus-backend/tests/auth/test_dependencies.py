"""Pruebas unitarias para dependencias de seguridad y RBAC con Amazon Cognito (get_current_user y require_admin)."""

from unittest.mock import AsyncMock
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier
from nexus_backend.auth.presentation.dependencies import get_current_user, require_admin


class TestGetCurrentUserDependency:
    """Suite de pruebas para la resolución y autenticación de tokens contra Amazon Cognito."""

    @pytest.mark.asyncio
    async def test_cognito_jwt_happy_path_resolves_active_user(
        self, dummy_user: User
    ) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_cognito_jwt")
        mock_verifier = AsyncMock(spec=CognitoTokenVerifier)
        mock_verifier.verify_token.return_value = dummy_user

        authenticated_user = await get_current_user(credentials, verifier=mock_verifier)

        mock_verifier.verify_token.assert_called_once_with("valid_cognito_jwt")
        assert authenticated_user.id == dummy_user.id
        assert authenticated_user.email == dummy_user.email
        assert authenticated_user.role == "user"
        assert authenticated_user.is_admin is False

    @pytest.mark.asyncio
    async def test_banned_user_raises_403_forbidden(
        self, dummy_banned_user: User
    ) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="banned_jwt")
        mock_verifier = AsyncMock(spec=CognitoTokenVerifier)
        mock_verifier.verify_token.return_value = dummy_banned_user

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, verifier=mock_verifier)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "suspended or banned" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_invalid_token_propagates_unauthorized_exception(self) -> None:
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_jwt")
        mock_verifier = AsyncMock(spec=CognitoTokenVerifier)
        mock_verifier.verify_token.side_effect = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials, verifier=mock_verifier)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestRequireAdminGuard:
    """Suite de pruebas para el guardia de autorización RBAC (require_admin)."""

    @pytest.mark.asyncio
    async def test_admin_user_passes_authorization_guard(
        self, dummy_admin: User
    ) -> None:
        authorized_user = await require_admin(current_user=dummy_admin)
        assert authorized_user == dummy_admin
        assert authorized_user.is_admin is True

    @pytest.mark.asyncio
    async def test_normal_user_is_strictly_blocked_with_403(
        self, dummy_user: User
    ) -> None:
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user=dummy_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin role required" in exc_info.value.detail
