"""Pruebas unitarias rigurosas para dependencias de seguridad y RBAC (get_current_user y require_admin)."""

from unittest.mock import AsyncMock, patch
from uuid import UUID
import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import get_current_user, require_admin


class TestGetCurrentUserDependency:
    """Suite de pruebas para la resolución y autenticación de tokens contra Neon Auth."""

    @pytest.mark.asyncio
    async def test_session_token_happy_path_resolves_active_user(
        self, dummy_user: User
    ) -> None:
        # Arrange
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_neon_session_token_123")
        mock_session = AsyncMock()

        with patch(
            "nexus_backend.auth.presentation.dependencies.NeonAuthUserRepository"
        ) as mock_repo_cls:
            mock_repo_instance = mock_repo_cls.return_value
            mock_repo_instance.get_by_session_token = AsyncMock(return_value=dummy_user)

            # Act
            authenticated_user = await get_current_user(credentials, session=mock_session)

            # Assert - Spying y Contratos
            mock_repo_cls.assert_called_once_with(mock_session)
            mock_repo_instance.get_by_session_token.assert_called_once_with("valid_neon_session_token_123")
            # Regla de negocio: Debe retornar la entidad User con identidad intacta
            assert authenticated_user.id == dummy_user.id
            assert authenticated_user.email == dummy_user.email
            assert authenticated_user.role == "user"
            assert authenticated_user.is_admin is False

    @pytest.mark.asyncio
    async def test_jwt_token_with_uuid_sub_resolves_user(
        self, dummy_user: User
    ) -> None:
        # Arrange
        # Crear un JWT válido simulando token firmado por Neon Auth (clave de 32 bytes)
        token = jwt.encode(
            {"sub": str(dummy_user.id), "email": dummy_user.email},
            "super_secret_test_key_32_bytes_len!",
            algorithm="HS256",
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        mock_session = AsyncMock()

        with patch(
            "nexus_backend.auth.presentation.dependencies.NeonAuthUserRepository"
        ) as mock_repo_cls:
            mock_repo_instance = mock_repo_cls.return_value
            mock_repo_instance.get_by_session_token = AsyncMock(return_value=None)
            mock_repo_instance.get_by_id = AsyncMock(return_value=dummy_user)

            # Act
            authenticated_user = await get_current_user(credentials, session=mock_session)

            # Assert
            mock_repo_instance.get_by_id.assert_called_once_with(dummy_user.id)
            assert authenticated_user == dummy_user

    @pytest.mark.asyncio
    async def test_banned_user_raises_403_forbidden_with_audit_detail(
        self, dummy_banned_user: User
    ) -> None:
        # Arrange
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="banned_session_token")
        mock_session = AsyncMock()

        with patch(
            "nexus_backend.auth.presentation.dependencies.NeonAuthUserRepository"
        ) as mock_repo_cls:
            mock_repo_instance = mock_repo_cls.return_value
            mock_repo_instance.get_by_session_token = AsyncMock(return_value=dummy_banned_user)

            # Act & Assert
            # Regla de seguridad: Un usuario con flag 'banned=True' en Neon Auth debe ser
            # bloqueado inmediatamente con HTTP 403 Forbidden antes de acceder a cualquier recurso.
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, session=mock_session)

            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert "suspended or banned" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_nonexistent_or_expired_token_raises_401_unauthorized(self) -> None:
        # Arrange
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid_ghost_token")
        mock_session = AsyncMock()

        with patch(
            "nexus_backend.auth.presentation.dependencies.NeonAuthUserRepository"
        ) as mock_repo_cls:
            mock_repo_instance = mock_repo_cls.return_value
            mock_repo_instance.get_by_session_token = AsyncMock(return_value=None)

            # Act & Assert
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(credentials, session=mock_session)

            # Regla de seguridad: Fallo de autenticación debe incluir header WWW-Authenticate
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
            assert "Invalid or expired authentication credentials" in exc_info.value.detail


class TestRequireAdminGuard:
    """Suite de pruebas para el guardia de autorización RBAC (require_admin)."""

    @pytest.mark.asyncio
    async def test_admin_user_passes_authorization_guard(
        self, dummy_admin: User
    ) -> None:
        # Arrange & Act
        authorized_user = await require_admin(current_user=dummy_admin)

        # Assert
        # Regla de negocio: El usuario administrador debe pasar sin mutaciones
        assert authorized_user == dummy_admin
        assert authorized_user.is_admin is True

    @pytest.mark.asyncio
    async def test_normal_user_is_strictly_blocked_with_403(
        self, dummy_user: User
    ) -> None:
        # Arrange & Act & Assert
        # Regla de negocio: Un usuario normal (role='user' o 'customer') NO puede ejecutar operaciones
        # administrativas sobre el catálogo (crear, modificar o eliminar videojuegos).
        with pytest.raises(HTTPException) as exc_info:
            await require_admin(current_user=dummy_user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Admin role required" in exc_info.value.detail
