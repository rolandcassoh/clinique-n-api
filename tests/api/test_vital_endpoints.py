"""Tests API — module vital."""
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.dependencies import get_current_user
from app.database import get_db, Base
from app.shared.exceptions.domain import DomainException

import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.vital.infrastructure.models  # noqa: F401

from app.modules.vital.api.router import router as vital_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

DOCTOR_USER_ID = 10
PATIENT_USER_ID = 20
OTHER_PATIENT_ID = 21


def _build_app() -> FastAPI:
    app = FastAPI(title="test-vital")
    app.include_router(vital_router, prefix="/api")

    @app.exception_handler(DomainException)
    async def _domain(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


@pytest_asyncio.fixture(scope="module", autouse=True)
async def _tables() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with _Session() as session:
        yield session
        await session.rollback()


def _make_client(db: AsyncSession, user_id: int, roles: list[str]) -> AsyncClient:
    from app.core.auth.jwt_handler import JWTHandler
    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    token = JWTHandler.create_access_token(user_id=user_id, roles=roles)
    app = _build_app()

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": user_id, "roles": roles}

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_redis] = _fake_redis

    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest_asyncio.fixture
async def doctor_client(db: AsyncSession) -> AsyncClient:
    async with _make_client(db, DOCTOR_USER_ID, ["doctor"]) as client:
        yield client


@pytest_asyncio.fixture
async def patient_client(db: AsyncSession) -> AsyncClient:
    async with _make_client(db, PATIENT_USER_ID, ["patient"]) as client:
        yield client


@pytest_asyncio.fixture
async def anon_client(db: AsyncSession) -> AsyncClient:
    app = _build_app()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


# ── Tests POST /api/vitals ────────────────────────────────────────────────────

class TestCreateVital:
    @pytest.mark.asyncio
    async def test_create_vital_201_doctor(self, db: AsyncSession, doctor_client: AsyncClient) -> None:
        resp = await doctor_client.post(
            "/api/vitals",
            json={
                "patient_id": PATIENT_USER_ID,
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "temperature": "37.2",
                "weight": "70.5",
                "height": "175.0",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["patient_id"] == PATIENT_USER_ID
        assert data["heart_rate"] == 72
        assert data["recorded_by"] == DOCTOR_USER_ID

    @pytest.mark.asyncio
    async def test_create_vital_bmi_calcule(self, db: AsyncSession, doctor_client: AsyncClient) -> None:
        resp = await doctor_client.post(
            "/api/vitals",
            json={
                "patient_id": PATIENT_USER_ID,
                "weight": "80",
                "height": "200",  # BMI = 80 / (2)^2 = 20
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["bmi"] is not None
        assert abs(data["bmi"] - 20.0) < 0.1

    @pytest.mark.asyncio
    async def test_create_vital_401_sans_auth(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/vitals",
            json={"patient_id": 1, "heart_rate": 72},
        )
        assert resp.status_code == 401


# ── Tests GET /api/vitals ─────────────────────────────────────────────────────

class TestListMyVitals:
    @pytest.mark.asyncio
    async def test_get_vitals_200_patient_retourne_les_siennes(
        self, db: AsyncSession, doctor_client: AsyncClient, patient_client: AsyncClient
    ) -> None:
        # Le médecin crée 2 vitals pour le patient
        for hr in [70, 75]:
            await doctor_client.post(
                "/api/vitals",
                json={"patient_id": PATIENT_USER_ID, "heart_rate": hr},
            )
        # Le médecin crée 1 vital pour un autre patient
        await doctor_client.post(
            "/api/vitals",
            json={"patient_id": OTHER_PATIENT_ID, "heart_rate": 90},
        )

        # Le patient ne voit que les siennes
        resp = await patient_client.get("/api/vitals")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["data"]:
            assert item["patient_id"] == PATIENT_USER_ID

    @pytest.mark.asyncio
    async def test_get_vitals_401_sans_auth(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/vitals")
        assert resp.status_code == 401


# ── Tests GET /api/vitals/stats ───────────────────────────────────────────────

class TestVitalStats:
    @pytest.mark.asyncio
    async def test_stats_retourne_dict_avec_dernieres_valeurs(
        self, db: AsyncSession, doctor_client: AsyncClient, patient_client: AsyncClient
    ) -> None:
        # Crée quelques vitals
        await doctor_client.post(
            "/api/vitals",
            json={
                "patient_id": PATIENT_USER_ID,
                "heart_rate": 80,
                "weight": "75.0",
                "height": "170.0",
            },
        )
        resp = await patient_client.get("/api/vitals/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "patient_id" in data
        assert data["patient_id"] == PATIENT_USER_ID
        # Les dernières valeurs doivent être présentes
        assert "last_heart_rate" in data
        assert "last_weight" in data
        assert "last_bmi" in data

    @pytest.mark.asyncio
    async def test_stats_401_sans_auth(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/vitals/stats")
        assert resp.status_code == 401


# ── Tests Admin GET /api/admin/vitals ─────────────────────────────────────────

class TestAdminVitals:
    @pytest.mark.asyncio
    async def test_admin_vitals_retourne_tous(self, db: AsyncSession, doctor_client: AsyncClient) -> None:
        resp = await doctor_client.get("/api/admin/vitals")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_admin_vitals_filtre_patient(self, db: AsyncSession, doctor_client: AsyncClient) -> None:
        resp = await doctor_client.get(f"/api/admin/vitals?patient_id={PATIENT_USER_ID}")
        assert resp.status_code == 200
        data = resp.json()
        for item in data["data"]:
            assert item["patient_id"] == PATIENT_USER_ID
