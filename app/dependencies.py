from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache.redis_client import get_redis
from app.database import get_db
from app.modules.auth.infrastructure.depots import SQLAlchemyUserRepository


async def get_user_repository(
    db: AsyncSession = Depends(get_db),
) -> SQLAlchemyUserRepository:
    return SQLAlchemyUserRepository(db)
