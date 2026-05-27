"""Tests API — module clinic."""
from datetime import date, time, datetime, timezone
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

# Import des modèles pour SQLite en mémoire
import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.clinic.infrastructure.models  # noqa: F401

from app.modules.clinic.api.router import router as clinic_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

ADMIN_USER_ID = 999
PATIENT_USER_ID = 1


def _build_app() -> FastAPI:
    app = FastAPI(title="test-clinic")
    app.include_router(clinic_router, prefix="/api")

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


@pytest_asyncio.fixture
async def anon_client(db: AsyncSession) -> AsyncClient:
    """Client sans authentification."""
    app = _build_app()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def admin_client(db: AsyncSession) -> AsyncClient:
    """Client admin authentifié."""
    from app.core.auth.jwt_handler import JWTHandler
    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    token = JWTHandler.create_access_token(user_id=ADMIN_USER_ID, roles=["admin", "super-admin"])

    app = _build_app()

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": ADMIN_USER_ID, "roles": ["admin", "super-admin"]}

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_redis] = _fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def patient_client(db: AsyncSession) -> AsyncClient:
    """Client patient authentifié (pas admin)."""
    from app.core.auth.jwt_handler import JWTHandler
    from app.core.cache.redis_client import get_redis
    from unittest.mock import AsyncMock, MagicMock

    token = JWTHandler.create_access_token(user_id=PATIENT_USER_ID, roles=["patient"])

    app = _build_app()

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": PATIENT_USER_ID, "roles": ["patient"]}

    fake_redis = MagicMock()
    fake_redis.get = AsyncMock(return_value=None)

    async def _fake_redis():
        yield fake_redis

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user
    app.dependency_overrides[get_redis] = _fake_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


# ── Tests GET /api/clinics ────────────────────────────────────────────────────

class TestListClinics:
    @pytest.mark.asyncio
    async def test_list_clinics_200_retourne_page(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/clinics")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)

    @pytest.mark.asyncio
    async def test_list_clinics_filtres_acceptes(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/clinics?page=1&per_page=5&search=test")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_clinics_avec_is_featured(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/clinics?is_featured=true")
        assert resp.status_code == 200


# ── Tests GET /api/clinic-categories ─────────────────────────────────────────

class TestListCategories:
    @pytest.mark.asyncio
    async def test_list_categories_200(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/clinic-categories")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── Tests GET /api/doctors ────────────────────────────────────────────────────

class TestListDoctors:
    @pytest.mark.asyncio
    async def test_list_doctors_200(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/doctors")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_list_doctors_filtres(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/doctors?speciality=cardiologie&min_fee=50")
        assert resp.status_code == 200


# ── Tests GET /api/doctors/{id} ───────────────────────────────────────────────

class TestGetDoctor:
    @pytest.mark.asyncio
    async def test_get_doctor_404_si_inexistant(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/doctors/999999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_doctor_200_si_existant(self, db: AsyncSession, anon_client: AsyncClient) -> None:
        """Crée un médecin, puis le récupère."""
        from app.modules.auth.infrastructure.models import UserModel
        from app.modules.clinic.infrastructure.models import ClinicModel, DoctorModel
        from app.core.auth.password import hash_password

        # Crée un user
        user = UserModel(
            id=100, name="Dr. Smith", email="smith@clinic.test",
            password=hash_password("Password1!"), is_active=True,
        )
        db.add(user)

        # Crée une clinique
        clinic = ClinicModel(
            id=100, owner_id=100, name="Test Clinic", slug="test-clinic-100",
            is_active=True, is_featured=False, commission_rate=Decimal("0"),
        )
        db.add(clinic)

        # Crée un médecin
        doctor = DoctorModel(
            id=100, user_id=100, clinic_id=100,
            speciality="cardiologie",
            experience_years=5,
            consultation_fee=Decimal("100"),
            advance_payment_amount=Decimal("30"),
            is_available=True,
        )
        db.add(doctor)
        await db.flush()

        resp = await anon_client.get("/api/doctors/100")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 100
        assert data["speciality"] == "cardiologie"


# ── Tests GET /api/doctors/{id}/slots ────────────────────────────────────────

class TestGetAvailableSlots:
    @pytest.mark.asyncio
    async def test_slots_retourne_liste(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/doctors/1/slots?date=2030-06-02")
        assert resp.status_code == 200
        data = resp.json()
        assert "slots" in data
        assert isinstance(data["slots"], list)

    @pytest.mark.asyncio
    async def test_slots_date_passee_retourne_vide(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/doctors/1/slots?date=2000-01-01")
        assert resp.status_code == 200
        assert resp.json()["slots"] == []


# ── Tests POST /api/doctors/{id}/ratings ─────────────────────────────────────

class TestRateDoctor:
    @pytest.mark.asyncio
    async def test_rate_doctor_401_sans_auth(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/doctors/1/ratings",
            json={"rating": 5, "comment": "Excellent"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_rate_doctor_avec_auth(self, db: AsyncSession, patient_client: AsyncClient) -> None:
        """Tente une notation (peut échouer si le médecin n'existe pas, mais pas 401)."""
        resp = await patient_client.post(
            "/api/doctors/999999/ratings",
            json={"rating": 4},
        )
        # Si le médecin n'existe pas, 409 (pas de duplicate) ou erreur DB
        # Mais pas 401
        assert resp.status_code != 401


# ── Tests Admin — créer clinique ──────────────────────────────────────────────

class TestAdminCreateClinic:
    @pytest.mark.asyncio
    async def test_create_clinic_201_admin(self, db: AsyncSession, admin_client: AsyncClient) -> None:
        from app.modules.auth.infrastructure.models import UserModel
        from app.core.auth.password import hash_password

        user = UserModel(
            id=200, name="Owner", email="owner@test.app",
            password=hash_password("Password1!"), is_active=True,
        )
        db.add(user)
        await db.flush()

        resp = await admin_client.post(
            "/api/admin/clinics",
            json={
                "owner_id": 200,
                "name": "Clinique Admin Test",
                "slug": "clinique-admin-test-unique-xyz",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Clinique Admin Test"

    @pytest.mark.asyncio
    async def test_create_clinic_401_sans_auth(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.post(
            "/api/admin/clinics",
            json={"owner_id": 1, "name": "Test", "slug": "test"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_create_clinic_409_slug_duplique(
        self, db: AsyncSession, admin_client: AsyncClient
    ) -> None:
        from app.modules.auth.infrastructure.models import UserModel
        from app.modules.clinic.infrastructure.models import ClinicModel
        from app.core.auth.password import hash_password

        user = UserModel(
            id=201, name="Owner2", email="owner2@test.app",
            password=hash_password("Password1!"), is_active=True,
        )
        db.add(user)
        clinic = ClinicModel(
            id=201, owner_id=201, name="Existante", slug="slug-existant-409",
            is_active=True, is_featured=False, commission_rate=Decimal("0"),
        )
        db.add(clinic)
        await db.flush()

        resp = await admin_client.post(
            "/api/admin/clinics",
            json={"owner_id": 201, "name": "Autre", "slug": "slug-existant-409"},
        )
        assert resp.status_code == 409
