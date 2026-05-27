"""Tests API des endpoints appointment."""
from __future__ import annotations

import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock

from app.database import get_db, Base
from app.core.cache.redis_client import get_redis
from app.core.auth.jwt_handler import JWTHandler
from app.shared.exceptions.domain import DomainException

# Importer les modèles pour créer les tables
import app.modules.appointment.infrastructure.models  # noqa: F401

from app.modules.appointment.api.router import router as appointment_router
from app.modules.appointment.api.webhooks import webhook_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


def _build_test_app() -> FastAPI:
    test_app = FastAPI(title="Appointment Test App")
    test_app.include_router(appointment_router, prefix="/api")
    test_app.include_router(webhook_router, prefix="/api")

    @test_app.exception_handler(DomainException)
    async def _domain_exc_handler(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return test_app


_test_app = _build_test_app()


def _fake_redis():
    fake = MagicMock()
    fake.get = AsyncMock(return_value=None)
    fake.delete = AsyncMock(return_value=True)
    fake.set = AsyncMock(return_value=True)
    return fake


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
async def api_client(db: AsyncSession):
    """Client non authentifié."""
    redis = _fake_redis()

    async def _override_db():
        yield db

    async def _override_redis():
        yield redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test"
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def patient_client(db: AsyncSession):
    """Client authentifié en tant que patient."""
    token = JWTHandler.create_access_token(user_id=42, roles=["patient"])
    headers = {"Authorization": f"Bearer {token}"}
    redis = _fake_redis()

    async def _override_db():
        yield db

    async def _override_redis():
        yield redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def doctor_client(db: AsyncSession):
    """Client authentifié en tant que médecin."""
    token = JWTHandler.create_access_token(user_id=10, roles=["doctor"])
    headers = {"Authorization": f"Bearer {token}"}
    redis = _fake_redis()

    async def _override_db():
        yield db

    async def _override_redis():
        yield redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(db: AsyncSession):
    """Client admin."""
    token = JWTHandler.create_access_token(user_id=999, roles=["admin", "super-admin"])
    headers = {"Authorization": f"Bearer {token}"}
    redis = _fake_redis()

    async def _override_db():
        yield db

    async def _override_redis():
        yield redis

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client

    _test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests : authentification
# ---------------------------------------------------------------------------


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_book_without_auth_returns_401(self, api_client: AsyncClient):
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
        }
        resp = await api_client.post("/api/appointments", json=payload)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_without_auth_returns_401(self, api_client: AsyncClient):
        resp = await api_client.get("/api/appointments")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_endpoint_without_auth_returns_401(self, api_client: AsyncClient):
        resp = await api_client.get("/api/admin/appointments")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests : création RDV
# ---------------------------------------------------------------------------


class TestBookAppointment:
    @pytest.mark.asyncio
    async def test_book_appointment_returns_201(self, patient_client: AsyncClient):
        scheduled = (datetime.utcnow() + timedelta(days=3)).replace(
            hour=9, minute=0, second=0, microsecond=0
        )
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "type": "in_person",
            "consultation_fee": "10000",
            "session_duration": 30,
        }
        resp = await patient_client.post("/api/appointments", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "reference" in data
        assert data["reference"].startswith("APT-")
        assert data["status"] == "pending"
        assert data["patient_id"] == 42

    @pytest.mark.asyncio
    async def test_book_duplicate_slot_returns_409(self, patient_client: AsyncClient):
        """Réserver le même créneau deux fois doit retourner 409."""
        scheduled = (datetime.utcnow() + timedelta(days=4)).replace(
            hour=14, minute=0, second=0, microsecond=0
        )
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "consultation_fee": "5000",
        }
        resp1 = await patient_client.post("/api/appointments", json=payload)
        assert resp1.status_code == 201
        resp2 = await patient_client.post("/api/appointments", json=payload)
        assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# Tests : liste RDVs
# ---------------------------------------------------------------------------


class TestListAppointments:
    @pytest.mark.asyncio
    async def test_list_returns_paginated_response(self, patient_client: AsyncClient):
        resp = await patient_client.get("/api/appointments")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    @pytest.mark.asyncio
    async def test_list_returns_only_own_appointments(self, patient_client: AsyncClient):
        """Le patient ne voit que ses propres RDVs."""
        scheduled = (datetime.utcnow() + timedelta(days=5)).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "consultation_fee": "5000",
        }
        await patient_client.post("/api/appointments", json=payload)
        resp = await patient_client.get("/api/appointments")
        assert resp.status_code == 200
        data = resp.json()
        for apt in data["data"]:
            assert apt["patient_id"] == 42


# ---------------------------------------------------------------------------
# Tests : confirmation par médecin
# ---------------------------------------------------------------------------


class TestDoctorConfirm:
    @pytest.mark.asyncio
    async def test_doctor_confirm_appointment(
        self, patient_client: AsyncClient, doctor_client: AsyncClient
    ):
        """Médecin confirme un RDV existant."""
        scheduled = (datetime.utcnow() + timedelta(days=6)).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        # Créer le RDV avec le patient (doctor_id=10 = user du doctor_client)
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "consultation_fee": "7500",
        }
        create_resp = await patient_client.post("/api/appointments", json=payload)
        assert create_resp.status_code == 201
        apt_id = create_resp.json()["id"]

        # Médecin confirme
        resp = await doctor_client.patch(f"/api/doctor/appointments/{apt_id}/confirm")
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"


# ---------------------------------------------------------------------------
# Tests : annulation
# ---------------------------------------------------------------------------


class TestCancelAppointment:
    @pytest.mark.asyncio
    async def test_cancel_appointment_returns_200(self, patient_client: AsyncClient):
        """Annulation d'un RDV lointain = remboursement total."""
        scheduled = (datetime.utcnow() + timedelta(days=7)).replace(
            hour=11, minute=0, second=0, microsecond=0
        )
        payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "consultation_fee": "10000",
        }
        create_resp = await patient_client.post("/api/appointments", json=payload)
        assert create_resp.status_code == 201
        apt_id = create_resp.json()["id"]

        # Annuler — httpx.delete() ne supporte pas json/content dans cette version
        # Utiliser request() comme alternative
        import json as _json
        resp = await patient_client.request(
            "DELETE",
            f"/api/appointments/{apt_id}",
            content=_json.dumps({"reason": "Raison valide pour annulation"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "refund_amount" in data
        assert "policy_applied" in data
        # RDV dans 7 jours = remboursement total
        assert data["policy_applied"] == "full"


# ---------------------------------------------------------------------------
# Tests : admin
# ---------------------------------------------------------------------------


class TestAdminEndpoints:
    @pytest.mark.asyncio
    async def test_admin_list_all_appointments(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/admin/appointments")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_admin_stats(self, admin_client: AsyncClient):
        resp = await admin_client.get("/api/admin/appointments/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_status" in data
        assert "total_revenue" in data

    @pytest.mark.asyncio
    async def test_patient_cannot_access_admin(self, patient_client: AsyncClient):
        resp = await patient_client.get("/api/admin/appointments")
        assert resp.status_code == 403
