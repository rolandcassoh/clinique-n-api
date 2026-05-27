"""Tests unitaires — domaine subscription (logique pure, sans I/O)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.modules.subscription.application.use_cases import (
    CancelSubscriptionUseCase,
    RenewSubscriptionUseCase,
    SubscribeUseCase,
)
from app.modules.subscription.domain.entities import Subscription, SubscriptionPlan
from app.modules.subscription.domain.exceptions import (
    ActiveSubscriptionExistsError,
    CannotRenewCancelledError,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_plan(
    id: int = 1,
    billing_period: str = "monthly",
    trial_days: int = 0,
    price: Decimal = Decimal("29.99"),
) -> SubscriptionPlan:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return SubscriptionPlan(
        id=id, name="Standard", slug="standard",
        description=None, price=price,
        billing_period=billing_period, trial_days=trial_days,
        is_active=True, is_featured=False, sort_order=0,
        created_at=now, updated_at=now,
    )


def _make_subscription(
    id: int = 1,
    clinic_id: int = 10,
    plan_id: int = 1,
    status: str = "active",
    days_ahead: int = 30,
    days_past: int = 0,
) -> Subscription:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    starts_at = now - timedelta(days=days_past)
    ends_at = now + timedelta(days=days_ahead)
    return Subscription(
        id=id, clinic_id=clinic_id, plan_id=plan_id, status=status,
        starts_at=starts_at, ends_at=ends_at,
        auto_renew=True, cancelled_at=None,
        created_at=starts_at, updated_at=starts_at,
    )


# ── SubscribeUseCase ──────────────────────────────────────────────────────────

class TestSubscribeUseCase:
    @pytest.mark.asyncio
    async def test_subscribe_sans_trial_cree_active(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        plan = _make_plan(trial_days=0, billing_period="monthly")
        plan_repo.get_by_id.return_value = plan
        sub_repo.get_active_for_clinic.return_value = None  # pas de sub existante

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        created_sub = _make_subscription(status="active")
        sub_repo.create.return_value = created_sub

        uc = SubscribeUseCase(plan_repo, sub_repo)
        result = await uc.execute(clinic_id=10, plan_id=1)

        sub_repo.create.assert_awaited_once()
        call_kwargs = sub_repo.create.call_args.kwargs
        assert call_kwargs["status"] == "active"
        # ends_at ≈ now + 30 jours
        delta = call_kwargs["ends_at"] - call_kwargs["starts_at"]
        assert abs(delta.days - 30) <= 1

    @pytest.mark.asyncio
    async def test_subscribe_avec_trial_cree_trial(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        plan = _make_plan(trial_days=14, billing_period="monthly")
        plan_repo.get_by_id.return_value = plan
        sub_repo.get_active_for_clinic.return_value = None

        sub_repo.create.return_value = _make_subscription(status="trial")

        uc = SubscribeUseCase(plan_repo, sub_repo)
        await uc.execute(clinic_id=10, plan_id=1)

        call_kwargs = sub_repo.create.call_args.kwargs
        assert call_kwargs["status"] == "trial"
        delta = call_kwargs["ends_at"] - call_kwargs["starts_at"]
        assert abs(delta.days - 14) <= 1

    @pytest.mark.asyncio
    async def test_subscribe_yearly_365_jours(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        plan = _make_plan(trial_days=0, billing_period="yearly")
        plan_repo.get_by_id.return_value = plan
        sub_repo.get_active_for_clinic.return_value = None
        sub_repo.create.return_value = _make_subscription(status="active", days_ahead=365)

        uc = SubscribeUseCase(plan_repo, sub_repo)
        await uc.execute(clinic_id=10, plan_id=1)

        call_kwargs = sub_repo.create.call_args.kwargs
        delta = call_kwargs["ends_at"] - call_kwargs["starts_at"]
        assert abs(delta.days - 365) <= 1

    @pytest.mark.asyncio
    async def test_subscribe_leve_erreur_si_sub_existante(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        sub_repo.get_active_for_clinic.return_value = _make_subscription()

        uc = SubscribeUseCase(plan_repo, sub_repo)
        with pytest.raises(ActiveSubscriptionExistsError):
            await uc.execute(clinic_id=10, plan_id=1)


# ── RenewSubscriptionUseCase ──────────────────────────────────────────────────

class TestRenewSubscriptionUseCase:
    @pytest.mark.asyncio
    async def test_renew_calcule_nouveau_ends_at(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sub = _make_subscription(status="active", days_ahead=5)  # se termine dans 5j
        plan = _make_plan(billing_period="monthly")  # +30 jours

        sub_repo.get_by_id.return_value = sub
        plan_repo.get_by_id.return_value = plan

        expected_ends_at = sub.ends_at + timedelta(days=30)
        renewed = _make_subscription(status="active", days_ahead=35)
        sub_repo.update.return_value = renewed

        uc = RenewSubscriptionUseCase(plan_repo, sub_repo)
        result = await uc.execute(subscription_id=1)

        call_kwargs = sub_repo.update.call_args.kwargs
        assert call_kwargs["status"] == "active"
        assert call_kwargs["auto_renew"] is True
        # ends_at ≈ sub.ends_at + 30j
        delta = call_kwargs["ends_at"] - sub.ends_at
        assert abs(delta.days - 30) <= 1

    @pytest.mark.asyncio
    async def test_renew_sub_expiree_prend_now_comme_base(self) -> None:
        """Si ends_at est dans le passé, la nouvelle base est now."""
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        sub = _make_subscription(status="expired", days_ahead=-5)  # expiré il y a 5j
        plan = _make_plan(billing_period="monthly")

        sub_repo.get_by_id.return_value = sub
        plan_repo.get_by_id.return_value = plan
        sub_repo.update.return_value = _make_subscription(status="active", days_ahead=30)

        uc = RenewSubscriptionUseCase(plan_repo, sub_repo)
        await uc.execute(subscription_id=1)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        call_kwargs = sub_repo.update.call_args.kwargs
        # new ends_at = max(now, sub.ends_at [dans le passé]) + 30j ≈ now + 30j
        delta = call_kwargs["ends_at"] - now
        assert abs(delta.days - 30) <= 1

    @pytest.mark.asyncio
    async def test_renew_cancelled_leve_erreur(self) -> None:
        plan_repo = AsyncMock()
        sub_repo = AsyncMock()

        sub = _make_subscription(status="cancelled")
        sub_repo.get_by_id.return_value = sub

        uc = RenewSubscriptionUseCase(plan_repo, sub_repo)
        with pytest.raises(CannotRenewCancelledError):
            await uc.execute(subscription_id=1)


# ── CancelSubscriptionUseCase ─────────────────────────────────────────────────

class TestCancelSubscriptionUseCase:
    @pytest.mark.asyncio
    async def test_cancel_met_status_cancelled_et_auto_renew_false(self) -> None:
        repo = AsyncMock()
        sub = _make_subscription(status="active")
        repo.get_by_id.return_value = sub

        cancelled_sub = _make_subscription(status="cancelled")
        cancelled_sub.auto_renew = False
        repo.update.return_value = cancelled_sub

        uc = CancelSubscriptionUseCase(repo)
        result = await uc.execute(subscription_id=1)

        call_kwargs = repo.update.call_args.kwargs
        assert call_kwargs["status"] == "cancelled"
        assert call_kwargs["auto_renew"] is False
        assert "cancelled_at" in call_kwargs

    @pytest.mark.asyncio
    async def test_cancel_appelle_update_avec_bon_id(self) -> None:
        repo = AsyncMock()
        sub = _make_subscription(id=42, status="trial")
        repo.get_by_id.return_value = sub
        repo.update.return_value = sub

        uc = CancelSubscriptionUseCase(repo)
        await uc.execute(subscription_id=42)

        repo.update.assert_awaited_once()
        call_args = repo.update.call_args
        assert call_args.args[0] == 42 or call_args.kwargs.get("subscription_id") == 42 or True
        # Vérifie que update a bien été appelé avec l'id correct
        assert repo.update.call_args[0][0] == 42
