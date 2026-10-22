"""Pruebas unitarias para la verificación de JWT de Amazon Cognito."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException

from nexus_backend.auth.infrastructure.cognito import CognitoTokenVerifier


class TestCognitoTokenVerifier:
    """Suite de validación para el verificador de tokens de Cognito."""

    @pytest.mark.asyncio
    async def test_verify_token_missing_kid_raises_401(self) -> None:
        verifier = CognitoTokenVerifier()
        # Token malformado o sin kid en cabecera
        with patch("jwt.get_unverified_header", return_value={}):
            with pytest.raises(HTTPException) as exc_info:
                await verifier.verify_token("mock.jwt.token")
            assert exc_info.value.status_code == 401
            assert "missing 'kid'" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_token_key_not_in_jwks_raises_401(self) -> None:
        verifier = CognitoTokenVerifier()
        with patch("jwt.get_unverified_header", return_value={"kid": "unknown_kid"}):
            verifier._get_jwks = AsyncMock(return_value={"keys": [{"kid": "other_kid"}]})
            with pytest.raises(HTTPException) as exc_info:
                await verifier.verify_token("mock.jwt.token")
            assert exc_info.value.status_code == 401
            assert "not found in Cognito JWKS" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_jwks_caching_and_lazy_load(self) -> None:
        verifier = CognitoTokenVerifier()
        mock_jwks = {"keys": [{"kid": "test_kid_1", "kty": "RSA"}]}

        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_jwks
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp

            # Primera llamada: debe realizar petición HTTP
            jwks1 = await verifier._get_jwks(force_refresh=False)
            assert jwks1 == mock_jwks

            # Segunda llamada: debe retornar la caché sin nueva petición
            jwks2 = await verifier._get_jwks(force_refresh=False)
            assert jwks2 == mock_jwks
            mock_get.assert_called_once()
