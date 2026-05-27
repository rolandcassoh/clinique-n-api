"""Tests API du module wallet."""
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import get_db, Base
from app.shared.exceptions.domain import DomainException
from app.core.auth.jwt_handler import JWTHandler

# Import des modèles
import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.wallet.infrastructure.models  # noqa: F401

from app.modules.wallet.api.router import router as wallet_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

from sqlalchemy import event

@event.listens_for(_engine.sync_engine, "connect")
def _disable_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()


def _build_test_app() -> FastAPI:
    test_app = FastAPI(title="Test Wallet")
    test_app.include_router(wallet_router, prefix="/api")

    @test_app.exception_handler(DomainException)
    async def _domain_exc(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return test_app


_test_app = _build_test_app()


@pytest_asyncio.fixture(scope="module", autouse=True)
async def _create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with _TestSessionLocal() as session:
        yield session
        await session.rollback()


def _make_client_fixture(user_id: int, roles: list[str]):
    @pytest_asyncio.fixture
    async def _client(db: AsyncSession) -> AsyncClient:
        token = JWTHandler.create_access_token(user_id=user_id, roles=roles)
        headers = {"Authorization": f"Bearer {token}"}

        async def _override_db():
            yield db

        from app.core.cache.redis_client import get_redis
        from unittest.mock import AsyncMock, MagicMock

        fake_redis = MagicMock()
        fake_redis.get = AsyncMock(return_value=None)

        async def _fake_redis():
            yield fake_redis

        _test_app.dependency_overrides[get_db] = _override_db
        _test_app.dependency_overrides[get_redis] = _fake_redis

        async with AsyncClient(
            transport=ASGITransport(app=_test_app), base_url="http://test", headers=headers
        ) as client:
            yield client

        _test_app.dependency_overrides.clear()

    return _client


@pytest_asyncio.fixture
async def patient_client(db: AsyncSession) -> AsyncClient:
    token = JWTHandler.create_access_token(user_id=10, roles=["patient"])
    headers = {"Authorization": f"Bearer {token}"}

    async def _override_db():
        yield db

    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test", headers=headers
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(db: AsyncSession) -> AsyncClient:
    token = JWTHandler.create_access_token(user_id=999, roles=["admin", "super-admin"])
    headers = {"Authorization": f"Bearer {token}"}

    async def _override_db():
        yield db

    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test", headers=headers
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_my_wallet_creates_if_absent(patient_client: AsyncClient):
    """GET /api/wallet → 200 avec balance 0 (wallet créé automatiquement)."""
    resp = await patient_client.get("/api/wallet")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == 10
    assert float(data["balance"]) == 0.0
    assert data["currency"] == "XAF"


@pytest.mark.asyncio
async def test_topup_wallet(patient_client: AsyncClient):
    """POST /api/wallet/topup → balance augmente."""
    # S'assurer que le wallet existe
    await patient_client.get("/api/wallet")

    resp = await patient_client.post(
        "/api/wallet/topup",
        json={"amount": 10000, "gateway": "stripe"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["balance"]) == 10000.0


@pytest.mark.asyncio
async def test_topup_multiple_times(patient_client: AsyncClient):
    """Plusieurs rechargements s'accumulent."""
    await patient_client.get("/api/wallet")
    await patient_client.post("/api/wallet/topup", json={"amount": 5000, "gateway": "stripe"})
    resp = await patient_client.post("/api/wallet/topup", json={"amount": 3000, "gateway": "razorpay"})
    assert resp.status_code == 200
    # La balance inclut aussi les autres tests — au moins 8000
    assert float(resp.json()["balance"]) >= 8000.0


@pytest.mark.asyncio
async def test_pay_appointment_insufficient_funds(patient_client: AsyncClient):
    """POST /api/wallet/pay-appointment solde insuffisant → 422."""
    # Le wallet a 0 XAF (ou peu), tenter de payer 50000
    await patient_client.get("/api/wallet")  # créer le wallet avec solde 0

    resp = await patient_client.post(
        "/api/wallet/pay-appointment",
        json={"appointment_id": 1, "amount": 999999},
    )
    assert resp.status_code == 422
    assert "insufficient" in resp.json()["detail"].lower() or "insuffisant" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_pay_appointment_success(patient_client: AsyncClient):
    """POST /api/wallet/pay-appointment → balance diminuée."""
    # Recharger d'abord
    await patient_client.get("/api/wallet")
    await patient_client.post("/api/wallet/topup", json={"amount": 20000, "gateway": "stripe"})

    # Récupérer le solde actuel
    wallet_resp = await patient_client.get("/api/wallet")
    balance_before = float(wallet_resp.json()["balance"])

    # Payer un RDV de 5000
    pay_resp = await patient_client.post(
        "/api/wallet/pay-appointment",
        json={"appointment_id": 42, "amount": 5000},
    )
    assert pay_resp.status_code == 200
    balance_after = float(pay_resp.json()["balance"])
    assert balance_after == balance_before - 5000.0


@pytest.mark.asyncio
async def test_wallet_history(patient_client: AsyncClient):
    """GET /api/wallet/history → historique paginé."""
    await patient_client.get("/api/wallet")
    await patient_client.post("/api/wallet/topup", json={"amount": 1000, "gateway": "test"})

    resp = await patient_client.get("/api/wallet/history")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_admin_list_wallets(admin_client: AsyncClient):
    """GET /api/admin/wallets → liste tous les wallets."""
    resp = await admin_client.get("/api/admin/wallets")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_admin_get_wallet_not_found(admin_client: AsyncClient):
    """GET /api/admin/wallets/{user_id} → 404 si wallet inexistant."""
    resp = await admin_client.get("/api/admin/wallets/88888")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_access_denied():
    """Accès sans token → 403 ou 401."""
    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/wallet")
        assert resp.status_code in (401, 403)
