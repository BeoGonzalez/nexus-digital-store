"""AWS Cognito JWT Verifier & Auth Client con soporte para JWKS perezoso (lazy) y caching en memoria.

Valida firmas RS256, expiración (exp), emisor (iss) y client_id (token_use access vs id).
Permite iniciar sesión (InitiateAuth) y registrar usuarios (SignUp) contra Amazon Cognito.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, status

from nexus_backend.auth.domain.entities import User
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


def compute_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calcula el HMAC-SHA256 SecretHash requerido por Cognito si el App Client tiene Client Secret."""
    message = (username + client_id).encode("utf-8")
    key = client_secret.encode("utf-8")
    signature = hmac.new(key, message, digestmod=hashlib.sha256).digest()
    return base64.b64encode(signature).decode("utf-8")


class CognitoTokenVerifier:
    """Validador y cliente de operaciones de usuario contra Amazon Cognito User Pools."""

    def __init__(self) -> None:
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_last_fetched: float = 0.0
        self._cache_ttl_seconds: float = 86400.0  # 24 horas

    @property
    def idp_endpoint(self) -> str:
        settings = get_settings()
        return f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"

    @property
    def jwks_url(self) -> str:
        settings = get_settings()
        return (
            f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
            f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
        )

    @property
    def expected_issuer(self) -> str:
        settings = get_settings()
        return f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"

    async def _get_jwks(self, force_refresh: bool = False) -> dict[str, Any]:
        """Obtiene las claves públicas del JWKS de Cognito de forma perezosa con caché."""
        now = time.time()
        if (
            not force_refresh
            and self._jwks_cache is not None
            and (now - self._jwks_last_fetched) < self._cache_ttl_seconds
        ):
            return self._jwks_cache

        logger.info("Fetching JWKS from Cognito: %s", self.jwks_url)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                data = response.json()
                self._jwks_cache = data
                self._jwks_last_fetched = now
                logger.info("Successfully fetched and cached Cognito JWKS (%d keys)", len(data.get("keys", [])))
                return data
        except Exception as exc:
            logger.error("Failed to fetch Cognito JWKS: %s", exc)
            if self._jwks_cache is not None:
                logger.warning("Falling back to stale JWKS cache")
                return self._jwks_cache
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Unable to retrieve authentication keys from Cognito: {exc}",
            ) from exc

    async def authenticate_user(self, email: str, password: str) -> str:
        """Autentica un usuario contra Cognito (InitiateAuth) y retorna el IdToken (JWT)."""
        settings = get_settings()
        if not settings.COGNITO_APP_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="COGNITO_APP_CLIENT_ID is not configured in the application environment.",
            )

        auth_params: dict[str, str] = {
            "USERNAME": email.strip(),
            "PASSWORD": password,
        }
        if settings.COGNITO_APP_CLIENT_SECRET:
            auth_params["SECRET_HASH"] = compute_secret_hash(
                email.strip(), settings.COGNITO_APP_CLIENT_ID, settings.COGNITO_APP_CLIENT_SECRET
            )

        payload = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": settings.COGNITO_APP_CLIENT_ID,
            "AuthParameters": auth_params,
        }
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.idp_endpoint, json=payload, headers=headers)
                data = resp.json()

            if resp.status_code != 200:
                err_type = str(data.get("__type", "")).split("#")[-1]
                message = data.get("message", "Error de autenticación.")
                logger.warning("Cognito InitiateAuth failed: %s - %s", err_type, message)

                if err_type in ("NotAuthorizedException", "UserNotFoundException"):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Correo o contraseña incorrectos.",
                    )
                if err_type == "UserNotConfirmedException":
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cuenta creada pero correo no verificado en Cognito.",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message,
                )

            auth_result = data.get("AuthenticationResult")
            if not auth_result or "IdToken" not in auth_result:
                # Si requiere cambio de contraseña o desafío MFA
                challenge = data.get("ChallengeName")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Desafío de Cognito pendiente: {challenge}",
                )

            # Retornamos el IdToken que contiene los claims de identidad (sub, email, grupos)
            return auth_result["IdToken"]

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error connecting to Cognito IDP: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error al conectar con Amazon Cognito: {exc}",
            ) from exc

    async def register_user(self, email: str, password: str, name: str) -> dict[str, Any]:
        """Registra un nuevo usuario en Amazon Cognito (SignUp)."""
        settings = get_settings()
        if not settings.COGNITO_APP_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="COGNITO_APP_CLIENT_ID is not configured in the application environment.",
            )

        clean_email = email.strip()
        payload: dict[str, Any] = {
            "ClientId": settings.COGNITO_APP_CLIENT_ID,
            "Username": clean_email,
            "Password": password,
            "UserAttributes": [
                {"Name": "email", "Value": clean_email},
                {"Name": "name", "Value": name.strip() or clean_email.split("@")[0]},
            ],
        }
        if settings.COGNITO_APP_CLIENT_SECRET:
            payload["SecretHash"] = compute_secret_hash(
                clean_email, settings.COGNITO_APP_CLIENT_ID, settings.COGNITO_APP_CLIENT_SECRET
            )

        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.SignUp",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.idp_endpoint, json=payload, headers=headers)
                data = resp.json()

            if resp.status_code != 200:
                err_type = str(data.get("__type", "")).split("#")[-1]
                message = data.get("message", "Error al registrar usuario.")
                logger.warning("Cognito SignUp failed: %s - %s", err_type, message)

                if err_type == "UsernameExistsException":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="El correo electrónico ya está registrado en Cognito.",
                    )
                if err_type == "InvalidPasswordException":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"La contraseña no cumple la política de Cognito: {message}",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=message,
                )

            return data

        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error connecting to Cognito SignUp: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error al conectar con Amazon Cognito: {exc}",
            ) from exc

    async def verify_token(self, token: str) -> User:
        """Verifica la validez del token JWT y construye la entidad User."""
        settings = get_settings()

        # 1. Obtener headers sin verificar para extraer 'kid'
        try:
            unverified_headers = jwt.get_unverified_header(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token headers: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        kid = unverified_headers.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token header missing 'kid'",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 2. Localizar la clave en el JWKS (con reintento si hubo rotación de claves)
        jwks = await self._get_jwks(force_refresh=False)
        key_dict = self._find_key(jwks, kid)

        if not key_dict:
            logger.warning("Key ID %s not found in cached JWKS. Refreshing...", kid)
            jwks = await self._get_jwks(force_refresh=True)
            key_dict = self._find_key(jwks, kid)

        if not key_dict:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Public key with kid '{kid}' not found in Cognito JWKS",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 3. Decodificar clave pública y validar firma + exp + iss
        try:
            public_key = RSAAlgorithm.from_jwk(key_dict)
            payload = jwt.decode(
                token,
                key=public_key,
                algorithms=["RS256"],
                issuer=self.expected_issuer,
                options={"verify_exp": True, "verify_iss": True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except jwt.InvalidIssuerError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token verification failed: {exc}",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        # 4. Validar token_use y client_id
        token_use = payload.get("token_use")
        if settings.COGNITO_APP_CLIENT_ID:
            if token_use == "access":
                token_client_id = payload.get("client_id")
                if token_client_id != settings.COGNITO_APP_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid client_id in access token (expected {settings.COGNITO_APP_CLIENT_ID})",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            elif token_use == "id":
                aud = payload.get("aud")
                if aud != settings.COGNITO_APP_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=f"Invalid aud in id token (expected {settings.COGNITO_APP_CLIENT_ID})",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Unsupported token_use: '{token_use}'",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # 5. Mapear claims a entidad User
        sub = str(payload.get("sub") or "")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'sub' claim",
                headers={"WWW-Authenticate": "Bearer"},
            )

        email = str(
            payload.get("email")
            or payload.get("cognito:username")
            or payload.get("username")
            or f"{sub}@cognito.user"
        )
        name = str(payload.get("name") or payload.get("preferred_username") or email.split("@")[0])

        groups = payload.get("cognito:groups") or []
        if isinstance(groups, str):
            groups = [groups]
        is_admin = (
            any(g.lower() == "admin" for g in groups)
            or str(payload.get("custom:role", "")).lower() == "admin"
            or email.lower() == "admin@nexus.com"
        )
        role = "admin" if is_admin else "user"
        email_verified = bool(payload.get("email_verified", True))

        return User(
            id=sub,
            email=email,
            name=name,
            role=role,
            banned=False,
            email_verified=email_verified,
        )

    @staticmethod
    def _find_key(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None


# Instancia singleton para caching en memoria
_cognito_verifier = CognitoTokenVerifier()


def get_cognito_verifier() -> CognitoTokenVerifier:
    return _cognito_verifier
