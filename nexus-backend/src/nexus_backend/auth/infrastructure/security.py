from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from nexus_backend.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_settings = get_settings()


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_jwt_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.JWT_EXPIRATION_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _settings.JWT_SECRET, algorithm=_settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, _settings.JWT_SECRET, algorithms=[_settings.JWT_ALGORITHM])
