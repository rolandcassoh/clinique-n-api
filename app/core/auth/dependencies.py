from collections.abc import Callable
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.jwt_handler import JWTHandler
from app.core.cache.redis_client import get_redis
from app.database import get_db

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
    redis: Any = Depends(get_redis),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    token_hash = JWTHandler.hash_token(token)
    is_revoked = await redis.get(f"token:blacklist:{token_hash}")
    if is_revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )

    try:
        payload = JWTHandler.decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "id": int(payload["sub"]),
        "roles": payload.get("roles", []),
        "token": token,
        "payload": payload,
    }


def require_role(*roles: str) -> Callable[..., Any]:
    async def _check(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_roles: list[str] = user.get("roles", [])
        if not any(r in user_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role(s): {list(roles)}",
            )
        return user

    return _check


def require_permission(permission: str) -> Callable[..., Any]:
    async def _check(user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_permissions: list[str] = user.get("permissions", [])
        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return user

    return _check
