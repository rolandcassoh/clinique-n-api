import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config import settings


class JWTHandler:
    _algorithm: str = settings.jwt_algorithm
    _secret: str = settings.jwt_secret_key

    @classmethod
    def create_access_token(
        cls,
        user_id: int,
        roles: list[str],
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.jwt_access_token_expire_minutes
        )
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "type": "access",
            "roles": roles,
            "iat": datetime.now(UTC),
            "exp": expire,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, cls._secret, algorithm=cls._algorithm)

    @classmethod
    def create_refresh_token(cls, user_id: int) -> str:
        expire = datetime.now(UTC) + timedelta(
            days=settings.jwt_refresh_token_expire_days
        )
        payload: dict[str, Any] = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": datetime.now(UTC),
            "exp": expire,
        }
        return jwt.encode(payload, cls._secret, algorithm=cls._algorithm)

    @classmethod
    def decode(cls, token: str) -> dict[str, Any]:
        return jwt.decode(token, cls._secret, algorithms=[cls._algorithm])

    @classmethod
    def decode_access_token(cls, token: str) -> dict[str, Any]:
        payload = cls.decode(token)
        if payload.get("type") != "access":
            raise JWTError("Not an access token")
        return payload

    @classmethod
    def decode_refresh_token(cls, token: str) -> dict[str, Any]:
        payload = cls.decode(token)
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        return payload

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def remaining_ttl_seconds(payload: dict[str, Any]) -> int:
        exp = payload.get("exp", 0)
        remaining = int(exp) - int(datetime.now(UTC).timestamp())
        return max(remaining, 0)
