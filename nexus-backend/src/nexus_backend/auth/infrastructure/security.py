from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from nexus_backend.config import get_settings

_settings = get_settings()


class PasslibPasswordHasher:
    def hash(self, plain: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain.encode("utf-8")[:72], salt).decode("utf-8")

    def verify(self, plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
        except Exception:
            return False


class JwtTokenIssuer:
    def issue(self, subject: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=_settings.JWT_EXPIRATION_MINUTES)
        payload = {"sub": subject, "exp": expire}
        return jwt.encode(payload, _settings.JWT_SECRET, algorithm=_settings.JWT_ALGORITHM)


def decode_jwt_token(token: str) -> dict:
    return jwt.decode(token, _settings.JWT_SECRET, algorithms=[_settings.JWT_ALGORITHM])
