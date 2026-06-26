"""Tests API — module subscription."""
from decimal import Decimal
from datetime import datetime, timezone

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
import app.modules.clinic.infrastructure.models  # noqa: F401
import app.modules.abonnement.infrastructure.models  # noqa: F401

from app.modules.abonnement.api.routeur import router as subscription_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

ADMIN_USER_ID = 999
CLINIC_ADMIN_USER_ID = 50
CLINIC_ID = 10


def _build_app() -> FastAPI:
    app = FastAPI(title="test-subscription")
    app.include_router(subscription_router, prefix="/api")

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


def _make_client_ctx(db: AsyncSession, user_id: int, roles: list[str]) -> AsyncClient:
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
async def admin_client(db: AsyncSession) -> AsyncClient:
    async with _make_client_ctx(db, ADMIN_USER_ID, ["admin", "super-admin"]) as client:
        yield client


@pytest_asyncio.fixture
async def user_client(db: AsyncSession) -> AsyncClient:
    async with _make_client_ctx(db, CLINIC_ADMIN_USER_ID, ["clinic-admin"]) as client:
        yield client


@pytest_asyncio.fixture
async def anon_client(db: AsyncSession) -> AsyncClient:
    app = _build_app()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def seed_plan(db: AsyncSession):
    """Crée un plan de souscription en base."""
    from app.modules.abonnement.infrastructure.modeles import SubscriptionPlanModel
    plan = SubscriptionPlanModel(
        id=1,
        name="Starter",
        slug="starter-plan-test",
        price=Decimal("9.99"),
        billing_period="monthly",
        trial_days=0,
        is_active=True,
        is_featured=False,
        sort_order=1,
    )
    db.add(plan)
    await db.flush()
    return plan


@pytest_asyncio.fixture
async def seed_clinic(db: AsyncSession):
    """Crée une clinique en base."""
    from app.modules.auth.infrastructure.modeles import UserModel
    from app.modules.clinic.infrastructure.modeles import ClinicModel
    from app.core.auth.password import hash_password

    user = UserModel(
        id=CLINIC_ADMIN_USER_ID,
        name="Clinic Owner",
        email="owner@clinic-sub.test",
        password=hash_password("Password1!"),
        is_active=True,
    )
    db.add(user)

    clinic = ClinicModel(
        id=CLINIC_ID,
        owner_id=CLINIC_ADMIN_USER_ID,
        name="Test Subscription Clinic",
        slug="test-sub-clinic-xyz",
        is_active=True,
        is_featured=False,
        commission_rate=Decimal("0"),
    )
    db.add(clinic)
    await db.flush()
    return clinic


# ── Tests GET /api/subscription-plans ────────────────────────────────────────

class TestListPlans:
    @pytest.mark.asyncio
    async def test_list_plans_200_retourne_liste(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/subscription-plans")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    @pytest.mark.asyncio
    async def test_list_plans_avec_donnees(
        self, db: AsyncSession, anon_client: AsyncClient, seed_plan
    ) -> None:
        resp = await anon_client.get("/api/subscription-plans")
        assert resp.status_code == 200
        data = resp.json()
        slugs = [p["slug"] for p in data]
        assert "starter-plan-test" in slugs


# ── Tests GET /api/subscription-plans/{slug} ─────────────────────────────────

class TestGetPlan:
    @pytest.mark.asyncio
    async def test_get_plan_200(
        self, db: AsyncSession, anon_client: AsyncClient, seed_plan
    ) -> None:
        resp = await anon_client.get("/api/subscription-plans/starter-plan-test")
        assert resp.status_code == 200
        data = resp.json()
        assert data["slug"] == "starter-plan-test"
        assert "limitations" in data

    @pytest.mark.asyncio
    async def test_get_plan_404_inexistant(self, anon_client: AsyncClient) -> None:
        resp = await anon_client.get("/api/subscription-plans/plan-inexistant-xyz")
        assert resp.status_code == 404


# ── Tests POST /api/subscriptions ────────────────────────────────────────────

class TestSubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_201_dates_calculees(
        self, db: AsyncSession, user_client: AsyncClient, seed_plan, seed_clinic
    ) -> None:
        resp = await user_client.post(
            "/api/subscriptions",
            json={"plan_id": 1, "clinic_id": CLINIC_ID},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["clinic_id"] == CLINIC_ID
        assert data["plan_id"] == 1
        assert data["status"] in ("active", "trial")
        assert "starts_at" in data
        assert "ends_at" in data

        # ends_at > starts_at
        starts = datetime.fromisoformat(data["starts_at"])
        ends = datetime.fromisoformat(data["ends_at"])
        assert ends > starts

    @pytest.mark.asyncio
    async def test_subscribe_401_sans_auth(
        self, db: AsyncSession, anon_client: AsyncClient, seed_plan, seed_clinic
    ) -> None:
        resp = await anon_client.post(
            "/api/subscriptions",
            json={"plan_id": 1, "clinic_id": CLINIC_ID},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_subscribe_409_double_souscription(
        self, db: AsyncSession, user_client: AsyncClient, seed_plan, seed_clinic
    ) -> None:
        """La seconde souscription pour la même clinique doit lever un 409."""
        # Première souscription (peut déjà exister depuis le test précédent)
        await user_client.post(
            "/api/subscriptions",
            json={"plan_id": 1, "clinic_id": CLINIC_ID},
        )
        # Deuxième souscription → 409
        resp = await user_client.post(
            "/api/subscriptions",
            json={"plan_id": 1, "clinic_id": CLINIC_ID},
        )
        assert resp.status_code == 409


# ── Tests POST /api/subscriptions/{id}/cancel ────────────────────────────────

class TestCancelSubscription:
    @pytest.mark.asyncio
    async def test_cancel_subscription_status_cancelled(
        self, db: AsyncSession, user_client: AsyncClient, seed_plan
    ) -> None:
        """Crée une clinique séparée pour ce test, souscrit, puis annule."""
        from app.modules.auth.infrastructure.modeles import UserModel
        from app.modules.clinic.infrastructure.modeles import ClinicModel
        from app.core.auth.password import hash_password

        user = UserModel(
            id=300, name="Cancel Owner", email="cancel@clinic.test",
            password=hash_password("Password1!"), is_active=True,
        )
        db.add(user)
        clinic = ClinicModel(
            id=300, owner_id=300, name="Cancel Clinic", slug="cancel-clinic-xyz",
            is_active=True, is_featured=False, commission_rate=Decimal("0"),
        )
        db.add(clinic)
        await db.flush()

        # Souscrit
        sub_resp = await user_client.post(
            "/api/subscriptions",
            json={"plan_id": 1, "clinic_id": 300},
        )
        assert sub_resp.status_code == 201
        sub_id = sub_resp.json()["id"]

        # Annule
        cancel_resp = await user_client.post(f"/api/subscriptions/{sub_id}/cancel")
        assert cancel_resp.status_code == 200
        data = cancel_resp.json()
        assert data["status"] == "cancelled"
        assert data["auto_renew"] is False

    @pytest.mark.asyncio
    async def test_cancel_404_inexistant(self, user_client: AsyncClient) -> None:
        resp = await user_client.post("/api/subscriptions/999999/cancel")
        assert resp.status_code == 404


# ── Tests Admin ───────────────────────────────────────────────────────────────

class TestAdminSubscriptions:
    @pytest.mark.asyncio
    async def test_admin_list_subscriptions_200(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.get("/api/admin/subscriptions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    @pytest.mark.asyncio
    async def test_admin_create_plan_201(self, admin_client: AsyncClient) -> None:
        resp = await admin_client.post(
            "/api/admin/subscription-plans",
            json={
                "name": "Premium",
                "slug": "premium-test-plan-xyz",
                "price": 49.99,
                "billing_period": "monthly",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Premium"

    @pytest.mark.asyncio
    async def test_admin_upsert_limitation(
        self, db: AsyncSession, admin_client: AsyncClient, seed_plan
    ) -> None:
        resp = await admin_client.post(
            "/api/admin/subscription-plans/1/limitations",
            json={"feature": "max_doctors", "value": "5"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["feature"] == "max_doctors"
        assert data["value"] == "5"
