from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from nexus_backend.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_settings = get_settings()


class PasslibPasswordHasher:
    def hash(self, plain: str) -> str:
        return _pwd_context.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd_context.verify(plain, hashed)


class JwtTokenIssuer:
    def issue(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.JWT_EXPIRATION_MINUTES)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, _settings.JWT_SECRET, algorithm=_settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, _settings.JWT_SECRET, algorithms=[_settings.JWT_ALGORITHM])
