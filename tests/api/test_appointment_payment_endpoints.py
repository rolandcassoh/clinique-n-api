"""Tests API des endpoints paiement appointment."""
from __future__ import annotations

import json
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, MagicMock

from app.database import get_db, Base
from app.core.cache.redis_client import get_redis
from app.core.auth.jwt_handler import JWTHandler
from app.shared.exceptions.domain import DomainException

# Importer le modèle pour créer les tables
import app.modules.rendez_vous.infrastructure.models  # noqa: F401

from app.modules.rendez_vous.api.routeur import router as appointment_router
from app.modules.rendez_vous.api.webhooks import webhook_router

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(
    bind=_engine, class_=AsyncSession, expire_on_commit=False
)


def _build_test_app() -> FastAPI:
    test_app = FastAPI(title="Payment Test App")
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
async def patient_client(db: AsyncSession):
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
async def unauthenticated_client(db: AsyncSession):
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


async def _create_test_appointment(client: AsyncClient, doctor_id: int = 10) -> dict:
    """Crée un RDV de test et retourne les données JSON."""
    scheduled = (datetime.utcnow() + timedelta(days=3)).replace(
        hour=9, minute=0, second=0, microsecond=0
    )
    payload = {
        "clinic_id": 1,
        "doctor_id": doctor_id,
        "scheduled_at": scheduled.isoformat(),
        "consultation_fee": "15000",
        "session_duration": 30,
    }
    resp = await client.post("/api/appointments", json=payload)
    assert resp.status_code == 201, f"Failed to create appointment: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Tests : Stripe PaymentIntent
# ---------------------------------------------------------------------------


class TestStripeIntent:
    @pytest.mark.asyncio
    async def test_create_stripe_intent_returns_200(self, patient_client: AsyncClient):
        apt = await _create_test_appointment(patient_client)
        apt_id = apt["id"]

        resp = await patient_client.post(
            f"/api/appointments/{apt_id}/stripe-intent",
            json={"currency": "XAF"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "client_secret" in data
        assert "payment_intent_id" in data

    @pytest.mark.asyncio
    async def test_stripe_intent_unknown_appointment_returns_404(
        self, patient_client: AsyncClient
    ):
        resp = await patient_client.post(
            "/api/appointments/99999/stripe-intent",
            json={"currency": "XAF"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_stripe_intent_unauthenticated_returns_401(
        self, unauthenticated_client: AsyncClient
    ):
        resp = await unauthenticated_client.post(
            "/api/appointments/1/stripe-intent",
            json={"currency": "XAF"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests : Paiement wallet
# ---------------------------------------------------------------------------


class TestWalletPayment:
    @pytest.mark.asyncio
    async def test_pay_with_wallet_returns_200(self, patient_client: AsyncClient):
        apt = await _create_test_appointment(patient_client)
        apt_id = apt["id"]

        resp = await patient_client.post(
            f"/api/appointments/{apt_id}/pay",
            json={"gateway": "wallet", "currency": "XAF"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "paid"
        assert data["gateway"] == "wallet"

    @pytest.mark.asyncio
    async def test_pay_with_stripe_gateway_returns_200(self, patient_client: AsyncClient):
        """Paiement Stripe retourne client_secret (stub)."""
        scheduled = (datetime.utcnow() + timedelta(days=5)).replace(
            hour=10, minute=30, second=0, microsecond=0
        )
        apt_payload = {
            "clinic_id": 1,
            "doctor_id": 10,
            "scheduled_at": scheduled.isoformat(),
            "consultation_fee": "20000",
        }
        create_resp = await patient_client.post("/api/appointments", json=apt_payload)
        assert create_resp.status_code == 201
        apt_id = create_resp.json()["id"]

        resp = await patient_client.post(
            f"/api/appointments/{apt_id}/pay",
            json={"gateway": "stripe", "currency": "XAF"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "gateway" in data

    @pytest.mark.asyncio
    async def test_pay_unknown_appointment_returns_404(self, patient_client: AsyncClient):
        resp = await patient_client.post(
            "/api/appointments/99999/pay",
            json={"gateway": "wallet"},
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests : Webhooks
# ---------------------------------------------------------------------------


class TestStripeWebhook:
    @pytest.mark.asyncio
    async def test_webhook_invalid_json_returns_400(
        self, unauthenticated_client: AsyncClient
    ):
        resp = await unauthenticated_client.post(
            "/api/webhooks/stripe",
            content=b"not-valid-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_empty_body_returns_400(
        self, unauthenticated_client: AsyncClient
    ):
        resp = await unauthenticated_client.post(
            "/api/webhooks/stripe",
            content=b"",
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_webhook_valid_event_returns_200(
        self, unauthenticated_client: AsyncClient
    ):
        event = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123",
                    "metadata": {},
                }
            },
        }
        resp = await unauthenticated_client.post(
            "/api/webhooks/stripe",
            content=json.dumps(event).encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "received"


class TestRazorpayWebhook:
    @pytest.mark.asyncio
    async def test_razorpay_webhook_invalid_json_returns_400(
        self, unauthenticated_client: AsyncClient
    ):
        resp = await unauthenticated_client.post(
            "/api/webhooks/razorpay",
            content=b"not-valid-json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_razorpay_webhook_valid_event_returns_200(
        self, unauthenticated_client: AsyncClient
    ):
        event = {
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_123",
                        "notes": {},
                    }
                }
            },
        }
        resp = await unauthenticated_client.post(
            "/api/webhooks/razorpay",
            content=json.dumps(event).encode(),
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests : statut paiement
# ---------------------------------------------------------------------------


class TestPaymentStatus:
    @pytest.mark.asyncio
    async def test_payment_status_returns_200(self, patient_client: AsyncClient):
        apt = await _create_test_appointment(patient_client)
        apt_id = apt["id"]

        resp = await patient_client.get(f"/api/appointments/{apt_id}/payment-status")
        assert resp.status_code == 200
        data = resp.json()
        assert "payment_status" in data
        assert "amount" in data
        assert "transactions" in data
