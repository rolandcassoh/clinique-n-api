"""Tests API — module promotion."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth.dependencies import get_current_user
from app.database import Base, get_db
from app.shared.exceptions.domain import DomainException

# Import des modèles pour créer les tables
import app.modules.promotion.infrastructure.models  # noqa: F401
import app.modules.auth.infrastructure.models  # noqa: F401

from app.modules.promotion.api.router import router as promotion_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

ADMIN_ID = 999
USER_ID = 1


def _build_app() -> FastAPI:
    app = FastAPI(title="test-promotion")
    app.include_router(promotion_router, prefix="/api")

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
async def admin_client(db: AsyncSession) -> AsyncClient:
    from app.core.auth.jwt_handler import JWTHandler

    token = JWTHandler.create_access_token(user_id=ADMIN_ID, roles=["admin", "super-admin"])
    headers = {"Authorization": f"Bearer {token}"}

    app = _build_app()

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": ADMIN_ID, "roles": ["admin", "super-admin"]}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def auth_client(db: AsyncSession) -> AsyncClient:
    """Client user normal authentifié (rôle patient)."""
    from app.core.auth.jwt_handler import JWTHandler

    token = JWTHandler.create_access_token(user_id=USER_ID, roles=["patient"])
    headers = {"Authorization": f"Bearer {token}"}

    app = _build_app()

    async def _override_db():
        yield db

    async def _override_user():
        return {"id": USER_ID, "roles": ["patient"]}

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client


@pytest_asyncio.fixture
async def unauth_client(db: AsyncSession) -> AsyncClient:
    app = _build_app()

    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def promo_active(db: AsyncSession) -> dict:
    """Insère une promo active valide en DB et retourne son dict."""
    from app.modules.promotion.infrastructure.models import PromotionModel

    now = datetime.now(timezone.utc)
    m = PromotionModel(
        code="TEST10",
        name="Remise 10%",
        type="percentage",
        value=Decimal("10"),
        usage_limit=100,
        usage_count=0,
        starts_at=now - timedelta(days=1),
        expires_at=now + timedelta(days=30),
        is_active=True,
        applicable_to="all",
    )
    db.add(m)
    await db.flush()
    return {"id": m.id, "code": m.code}


@pytest_asyncio.fixture
async def promo_expiree(db: AsyncSession) -> dict:
    """Insère une promo expirée en DB."""
    from app.modules.promotion.infrastructure.models import PromotionModel

    now = datetime.now(timezone.utc)
    m = PromotionModel(
        code="EXPIRED",
        name="Promo expirée",
        type="fixed",
        value=Decimal("5"),
        usage_limit=None,
        usage_count=0,
        starts_at=now - timedelta(days=30),
        expires_at=now - timedelta(days=1),  # expirée hier
        is_active=True,
        applicable_to="all",
    )
    db.add(m)
    await db.flush()
    return {"id": m.id, "code": m.code}


# ── Tests POST /api/promotions/validate ──────────────────────────────────────


class TestValidatePromotion:
    @pytest.mark.asyncio
    async def test_code_valide_retourne_valid_true_et_discount(
        self,
        auth_client: AsyncClient,
        promo_active: dict,
    ) -> None:
        resp = await auth_client.post(
            "/api/promotions/validate",
            json={
                "code": promo_active["code"],
                "amount": 200.0,
                "applicable_to": "all",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["discount_amount"] == pytest.approx(20.0)  # 10% de 200
        assert data["promotion"] is not None

    @pytest.mark.asyncio
    async def test_code_expire_retourne_valid_false(
        self,
        auth_client: AsyncClient,
        promo_expiree: dict,
    ) -> None:
        resp = await auth_client.post(
            "/api/promotions/validate",
            json={
                "code": promo_expiree["code"],
                "amount": 100.0,
                "applicable_to": "all",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False
        assert data["discount_amount"] == 0.0

    @pytest.mark.asyncio
    async def test_code_inexistant_retourne_valid_false(
        self,
        auth_client: AsyncClient,
    ) -> None:
        resp = await auth_client.post(
            "/api/promotions/validate",
            json={
                "code": "DOESNOTEXIST",
                "amount": 100.0,
                "applicable_to": "all",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_sans_auth_retourne_401(
        self, unauth_client: AsyncClient
    ) -> None:
        resp = await unauth_client.post(
            "/api/promotions/validate",
            json={"code": "TEST10", "amount": 100.0, "applicable_to": "all"},
        )
        assert resp.status_code == 401


# ── Tests GET /api/admin/promotions ──────────────────────────────────────────


class TestAdminPromotions:
    @pytest.mark.asyncio
    async def test_list_promotions_sans_auth_retourne_401(
        self, unauth_client: AsyncClient
    ) -> None:
        resp = await unauth_client.get("/api/admin/promotions")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_promotions_admin_retourne_200(
        self, admin_client: AsyncClient
    ) -> None:
        resp = await admin_client.get("/api/admin/promotions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_create_promotion_admin_retourne_201(
        self, admin_client: AsyncClient
    ) -> None:
        payload = {
            "code": "NEWPROMO",
            "name": "Nouvelle promo",
            "type": "fixed",
            "value": "25.00",
            "is_active": True,
            "applicable_to": "all",
        }
        resp = await admin_client.post("/api/admin/promotions", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["code"] == "NEWPROMO"
        assert data["type"] == "fixed"

    @pytest.mark.asyncio
    async def test_create_promotion_code_duplique_retourne_409(
        self, admin_client: AsyncClient, promo_active: dict
    ) -> None:
        payload = {
            "code": promo_active["code"],  # code déjà existant
            "name": "Doublon",
            "type": "fixed",
            "value": "5.00",
            "is_active": True,
            "applicable_to": "all",
        }
        resp = await admin_client.post("/api/admin/promotions", json=payload)
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_delete_promotion_inexistante_retourne_404(
        self, admin_client: AsyncClient
    ) -> None:
        resp = await admin_client.delete("/api/admin/promotions/99999")
        assert resp.status_code == 404
