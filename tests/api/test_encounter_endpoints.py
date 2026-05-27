"""Tests API du module encounter."""
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

# Import des modèles pour créer les tables
import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.appointment.infrastructure.models  # noqa: F401
import app.modules.encounter.infrastructure.models  # noqa: F401

from app.modules.encounter.api.router import router as encounter_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

# Désactiver les FK SQLite sur chaque connexion (pas de vrais JOIN cross-module en test)
from sqlalchemy import event

@event.listens_for(_engine.sync_engine, "connect")
def _disable_fk(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()


def _build_test_app() -> FastAPI:
    test_app = FastAPI(title="Test Encounter")
    test_app.include_router(encounter_router, prefix="/api")

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
async def doctor_client(db: AsyncSession) -> AsyncClient:
    token = JWTHandler.create_access_token(user_id=1, roles=["doctor"])
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
async def patient_client(db: AsyncSession) -> AsyncClient:
    token = JWTHandler.create_access_token(user_id=99, roles=["patient"])
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
async def test_create_encounter_as_doctor(doctor_client: AsyncClient):
    """POST /api/encounters → 201 (médecin)"""
    resp = await doctor_client.post(
        "/api/encounters",
        json={"patient_id": 99, "chief_complaint": "Douleur abdominale"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["doctor_id"] == 1
    assert data["patient_id"] == 99
    assert data["status"] == "open"
    assert data["chief_complaint"] == "Douleur abdominale"


@pytest.mark.asyncio
async def test_create_encounter_as_patient_forbidden(patient_client: AsyncClient):
    """Un patient ne peut pas créer de consultation."""
    resp = await patient_client.post(
        "/api/encounters",
        json={"patient_id": 99, "chief_complaint": "Test"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_encounter(doctor_client: AsyncClient):
    """GET /api/encounters/{id} → 200"""
    # Créer d'abord
    create_resp = await doctor_client.post(
        "/api/encounters",
        json={"patient_id": 50},
    )
    encounter_id = create_resp.json()["id"]

    resp = await doctor_client.get(f"/api/encounters/{encounter_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == encounter_id


@pytest.mark.asyncio
async def test_get_encounter_not_found(doctor_client: AsyncClient):
    resp = await doctor_client.get("/api/encounters/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_upsert_medical_report_authorized_doctor(doctor_client: AsyncClient):
    """Le médecin qui a créé la consultation peut créer un rapport médical."""
    create_resp = await doctor_client.post(
        "/api/encounters",
        json={"patient_id": 50},
    )
    assert create_resp.status_code == 201
    encounter_id = create_resp.json()["id"]

    report_resp = await doctor_client.post(
        f"/api/encounters/{encounter_id}/medical-report",
        json={
            "symptoms": "Fièvre 38.5°C",
            "diagnosis": "Grippe",
            "treatment": "Paracétamol",
            "blood_pressure": "120/80",
        },
    )
    assert report_resp.status_code == 201
    data = report_resp.json()
    assert data["symptoms"] == "Fièvre 38.5°C"
    assert data["diagnosis"] == "Grippe"


@pytest.mark.asyncio
async def test_get_medical_report_wrong_doctor_forbidden(
    doctor_client: AsyncClient,
    db: AsyncSession,
):
    """Un médecin différent ne peut pas accéder au rapport médical d'une consultation."""
    # Créer une consultation par le médecin 1
    create_resp = await doctor_client.post(
        "/api/encounters",
        json={"patient_id": 50},
    )
    encounter_id = create_resp.json()["id"]

    # Créer un rapport
    await doctor_client.post(
        f"/api/encounters/{encounter_id}/medical-report",
        json={"symptoms": "Test", "diagnosis": "Test"},
    )

    # Un autre médecin (user_id=2) tente d'accéder
    from app.core.auth.jwt_handler import JWTHandler
    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    token2 = JWTHandler.create_access_token(user_id=2, roles=["doctor"])
    headers2 = {"Authorization": f"Bearer {token2}"}

    async def _override_db():
        yield db

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    from app.modules.encounter.api.router import router as enc_router
    test_app2 = FastAPI()
    test_app2.include_router(enc_router, prefix="/api")
    test_app2.dependency_overrides[get_db] = _override_db
    test_app2.dependency_overrides[get_redis] = _fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=test_app2), base_url="http://test", headers=headers2
    ) as other_client:
        resp = await other_client.get(f"/api/encounters/{encounter_id}/medical-report")
        assert resp.status_code == 403


@pytest.mark.asyncio
async def test_my_encounters_returns_only_own(patient_client: AsyncClient, doctor_client: AsyncClient):
    """GET /api/my-encounters → uniquement les consultations du patient connecté."""
    # Créer une consultation pour le patient 99
    await doctor_client.post("/api/encounters", json={"patient_id": 99})
    await doctor_client.post("/api/encounters", json={"patient_id": 99})
    # Et une pour un autre patient
    await doctor_client.post("/api/encounters", json={"patient_id": 50})

    resp = await patient_client.get("/api/my-encounters")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    # Toutes les consultations retournées appartiennent au patient 99
    for enc in data["data"]:
        assert enc["patient_id"] == 99


@pytest.mark.asyncio
async def test_add_prescription(doctor_client: AsyncClient):
    """POST /api/encounters/{id}/prescriptions → 201"""
    create_resp = await doctor_client.post("/api/encounters", json={"patient_id": 50})
    encounter_id = create_resp.json()["id"]

    presc_resp = await doctor_client.post(
        f"/api/encounters/{encounter_id}/prescriptions",
        json={
            "medication_name": "Amoxicilline",
            "dosage": "500mg",
            "frequency": "3 fois par jour",
            "duration_days": 7,
        },
    )
    assert presc_resp.status_code == 201
    data = presc_resp.json()
    assert data["medication_name"] == "Amoxicilline"
    assert data["is_chronic"] is False


@pytest.mark.asyncio
async def test_delete_prescription(doctor_client: AsyncClient):
    """DELETE /api/encounters/{id}/prescriptions/{p_id} → 204"""
    create_resp = await doctor_client.post("/api/encounters", json={"patient_id": 50})
    encounter_id = create_resp.json()["id"]

    presc_resp = await doctor_client.post(
        f"/api/encounters/{encounter_id}/prescriptions",
        json={"medication_name": "Ibuprofène", "dosage": "400mg"},
    )
    presc_id = presc_resp.json()["id"]

    del_resp = await doctor_client.delete(
        f"/api/encounters/{encounter_id}/prescriptions/{presc_id}"
    )
    assert del_resp.status_code == 204
