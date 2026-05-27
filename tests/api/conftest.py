"""Conftest pour les tests API des modules world, faq, blog, page, service, request_service, logistic.

Crée une app FastAPI de test qui monte uniquement les routers des modules,
en surchargeant get_db avec SQLite en mémoire (aiosqlite).
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db
from app.shared.exceptions.domain import DomainException

# Imports des modèles pour créer les tables
import app.modules.world.infrastructure.models  # noqa: F401
import app.modules.faq.infrastructure.models  # noqa: F401
import app.modules.blog.infrastructure.models  # noqa: F401
import app.modules.page.infrastructure.models  # noqa: F401
import app.modules.tag.infrastructure.models  # noqa: F401
import app.modules.currency.infrastructure.models  # noqa: F401
import app.modules.language.infrastructure.models  # noqa: F401
import app.modules.slider.infrastructure.models  # noqa: F401
import app.modules.constant.infrastructure.models  # noqa: F401
import app.modules.auth.infrastructure.models  # noqa: F401  — crée la table users
import app.modules.service.infrastructure.models  # noqa: F401
import app.modules.request_service.infrastructure.models  # noqa: F401
import app.modules.logistic.infrastructure.models  # noqa: F401

from app.database import Base  # Doit être importé APRÈS les models

from app.modules.world.api.router import router as world_router
from app.modules.faq.api.router import router as faq_router
from app.modules.blog.api.router import router as blog_router
from app.modules.page.api.router import router as page_router
from app.modules.tag.api.router import router as tag_router
from app.modules.currency.api.router import router as currency_router
from app.modules.language.api.router import router as language_router
from app.modules.slider.api.router import router as slider_router
from app.modules.constant.api.router import router as constant_router
from app.modules.service.api.router import router as service_router
from app.modules.request_service.api.router import router as request_service_router
from app.modules.logistic.api.router import router as logistic_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


def _build_test_app() -> FastAPI:
    test_app = FastAPI(title="Test App")

    test_app.include_router(world_router, prefix="/api")
    test_app.include_router(faq_router, prefix="/api")
    test_app.include_router(blog_router, prefix="/api")
    test_app.include_router(page_router, prefix="/api")
    test_app.include_router(tag_router, prefix="/api")
    test_app.include_router(currency_router, prefix="/api")
    test_app.include_router(language_router, prefix="/api")
    test_app.include_router(slider_router, prefix="/api")
    test_app.include_router(constant_router, prefix="/api")
    test_app.include_router(service_router, prefix="/api")
    test_app.include_router(request_service_router, prefix="/api")
    test_app.include_router(logistic_router, prefix="/api")

    @test_app.exception_handler(DomainException)
    async def _domain_exc_handler(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return test_app


_test_app = _build_test_app()


@pytest_asyncio.fixture(scope="module", autouse=True)
async def _create_tables() -> None:  # type: ignore[misc]
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def api_client(db: AsyncSession) -> AsyncClient:
    async def _override_db():
        yield db

    _test_app.dependency_overrides[get_db] = _override_db

    # Override get_redis pour éviter la connexion Redis en test
    try:
        from app.core.cache.redis_client import get_redis
        from unittest.mock import AsyncMock, MagicMock

        fake_redis = MagicMock()
        fake_redis.get = AsyncMock(return_value=None)  # token non révoqué

        async def _fake_redis():
            yield fake_redis

        _test_app.dependency_overrides[get_redis] = _fake_redis
    except Exception:
        pass

    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test"
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(db: AsyncSession) -> AsyncClient:
    """Client avec headers admin valides (JWT réel via JWTHandler)."""
    from app.core.auth.jwt_handler import JWTHandler

    token = JWTHandler.create_access_token(user_id=999, roles=["admin", "super-admin"])
    headers = {"Authorization": f"Bearer {token}"}

    async def _override_db():
        yield db

    # Override aussi get_redis pour éviter la connexion Redis en test
    try:
        from app.core.cache.redis_client import get_redis
        from unittest.mock import AsyncMock, MagicMock

        fake_redis = MagicMock()
        fake_redis.get = AsyncMock(return_value=None)  # token non révoqué

        async def _fake_redis():
            yield fake_redis

        _test_app.dependency_overrides[get_redis] = _fake_redis
    except Exception:
        pass

    _test_app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()
