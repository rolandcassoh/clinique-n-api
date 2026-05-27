"""Tests API du module billing."""
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
import app.modules.appointment.infrastructure.models  # noqa: F401
import app.modules.billing.infrastructure.models  # noqa: F401

from app.modules.billing.api.router import router as billing_router

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
    test_app = FastAPI(title="Test Billing")
    test_app.include_router(billing_router, prefix="/api")

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


@pytest_asyncio.fixture
async def auth_client(db: AsyncSession) -> AsyncClient:
    token = JWTHandler.create_access_token(user_id=1, roles=["patient"])
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
async def test_get_appointment_billing_auto_creates(auth_client: AsyncClient):
    """GET /api/appointments/{id}/billing → 200 avec facture créée automatiquement."""
    resp = await auth_client.get(
        "/api/appointments/1/billing",
        params={"patient_id": 1, "consultation_fee": "15000"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["appointment_id"] == 1
    assert data["status"] == "draft"
    assert "reference" in data
    assert data["reference"].startswith("INV-")
    assert float(data["subtotal"]) == 15000.0


@pytest.mark.asyncio
async def test_get_appointment_billing_idempotent(auth_client: AsyncClient):
    """Deux appels successifs retournent la même facture."""
    params = {"patient_id": 2, "consultation_fee": "20000"}
    resp1 = await auth_client.get("/api/appointments/2/billing", params=params)
    resp2 = await auth_client.get("/api/appointments/2/billing", params=params)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["reference"] == resp2.json()["reference"]


@pytest.mark.asyncio
async def test_get_billing_by_id(auth_client: AsyncClient):
    """GET /api/billing/{id} → 200"""
    # Créer via get_or_create
    create_resp = await auth_client.get(
        "/api/appointments/3/billing",
        params={"patient_id": 1, "consultation_fee": "10000"},
    )
    billing_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/api/billing/{billing_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == billing_id


@pytest.mark.asyncio
async def test_get_billing_not_found(auth_client: AsyncClient):
    resp = await auth_client.get("/api/billing/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_billing_pdf_returns_content(auth_client: AsyncClient):
    """GET /api/billing/{id}/pdf → 200, content-type application/pdf ou text/html (fallback)."""
    create_resp = await auth_client.get(
        "/api/appointments/4/billing",
        params={"patient_id": 1, "consultation_fee": "15000"},
    )
    billing_id = create_resp.json()["id"]

    resp = await auth_client.get(f"/api/billing/{billing_id}/pdf")
    assert resp.status_code == 200
    ct = resp.headers.get("content-type", "")
    assert "application/pdf" in ct or "text/html" in ct
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_admin_update_billing_status(admin_client: AsyncClient, auth_client: AsyncClient):
    """PATCH /api/admin/billing/{id}/status → passage draft → issued → paid"""
    create_resp = await auth_client.get(
        "/api/appointments/5/billing",
        params={"patient_id": 1, "consultation_fee": "25000"},
    )
    billing_id = create_resp.json()["id"]

    # draft → issued
    resp = await admin_client.patch(
        f"/api/admin/billing/{billing_id}/status",
        json={"status": "issued"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "issued"

    # issued → paid
    resp2 = await admin_client.patch(
        f"/api/admin/billing/{billing_id}/status",
        json={"status": "paid"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "paid"


@pytest.mark.asyncio
async def test_admin_invalid_status_transition(admin_client: AsyncClient, auth_client: AsyncClient):
    """Transition invalide (paid → cancelled) → 422"""
    create_resp = await auth_client.get(
        "/api/appointments/6/billing",
        params={"patient_id": 1, "consultation_fee": "5000"},
    )
    billing_id = create_resp.json()["id"]

    # Passer en paid directement
    await admin_client.patch(
        f"/api/admin/billing/{billing_id}/status", json={"status": "issued"}
    )
    await admin_client.patch(
        f"/api/admin/billing/{billing_id}/status", json={"status": "paid"}
    )

    # Tenter de passer en cancelled depuis paid
    resp = await admin_client.patch(
        f"/api/admin/billing/{billing_id}/status", json={"status": "cancelled"}
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_my_invoices(auth_client: AsyncClient):
    """GET /api/my-invoices → liste paginée"""
    resp = await auth_client.get("/api/my-invoices")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data
