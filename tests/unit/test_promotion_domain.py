"""Tests unitaires — domaine Promotion (logique pure, sans I/O)."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.modules.promotion.application.cas_utilisation import ValidatePromotionUseCase
from app.modules.promotion.domain.entites import Promotion


# ── Helpers ──────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_promo(
    id: int = 1,
    code: str = "PROMO10",
    type: str = "percentage",
    value: Decimal = Decimal("10"),
    min_order_amount: Decimal | None = None,
    max_discount_amount: Decimal | None = None,
    usage_limit: int | None = None,
    usage_count: int = 0,
    starts_at: datetime | None = None,
    expires_at: datetime | None = None,
    is_active: bool = True,
    applicable_to: str = "all",
    deleted_at: datetime | None = None,
) -> Promotion:
    return Promotion(
        id=id,
        code=code,
        name="Promo test",
        type=type,
        value=value,
        min_order_amount=min_order_amount,
        max_discount_amount=max_discount_amount,
        usage_limit=usage_limit,
        usage_count=usage_count,
        starts_at=starts_at,
        expires_at=expires_at,
        is_active=is_active,
        applicable_to=applicable_to,
        created_at=_now(),
        deleted_at=deleted_at,
    )


# ── Tests validation : cas invalides ─────────────────────────────────────────


class TestPromotionValidation:
    @pytest.mark.asyncio
    async def test_code_inexistant_retourne_invalide(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = None

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="ABSENT", amount=Decimal("100"), applicable_to="all")

        assert result.valid is False
        assert result.discount_amount == Decimal("0")

    @pytest.mark.asyncio
    async def test_code_inactif_retourne_invalide(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(is_active=False)

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="PROMO10", amount=Decimal("100"), applicable_to="all")

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_code_expire_retourne_invalide(self) -> None:
        repo = AsyncMock()
        expired_promo = _make_promo(
            expires_at=_now() - timedelta(days=1)  # expiré hier
        )
        repo.get_by_code.return_value = expired_promo

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="PROMO10", amount=Decimal("100"), applicable_to="all")

        assert result.valid is False
        assert "expiré" in (result.reason or "").lower()

    @pytest.mark.asyncio
    async def test_code_pas_encore_actif_retourne_invalide(self) -> None:
        repo = AsyncMock()
        future_promo = _make_promo(
            starts_at=_now() + timedelta(days=10)  # commence dans 10 jours
        )
        repo.get_by_code.return_value = future_promo

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="PROMO10", amount=Decimal("100"), applicable_to="all")

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_usage_depasse_retourne_invalide(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(
            usage_limit=5,
            usage_count=5,  # limite atteinte
        )

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="PROMO10", amount=Decimal("100"), applicable_to="all")

        assert result.valid is False
        assert result.discount_amount == Decimal("0")

    @pytest.mark.asyncio
    async def test_montant_insuffisant_retourne_invalide(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(
            min_order_amount=Decimal("200"),
        )

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(code="PROMO10", amount=Decimal("50"), applicable_to="all")

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_applicable_to_non_correspondant_retourne_invalide(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(applicable_to="products")

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(
            code="PROMO10", amount=Decimal("100"), applicable_to="appointments"
        )

        assert result.valid is False


# ── Tests calcul discount ─────────────────────────────────────────────────────


class TestDiscountCalculation:
    def test_percentage_sans_cap(self) -> None:
        promo = _make_promo(type="percentage", value=Decimal("20"))
        discount = promo.calculate_discount(Decimal("100"))
        assert discount == Decimal("20")

    def test_percentage_avec_max_discount(self) -> None:
        promo = _make_promo(
            type="percentage",
            value=Decimal("50"),
            max_discount_amount=Decimal("30"),
        )
        # 50% de 200 = 100, mais cap à 30
        discount = promo.calculate_discount(Decimal("200"))
        assert discount == Decimal("30")

    def test_percentage_sous_le_cap(self) -> None:
        promo = _make_promo(
            type="percentage",
            value=Decimal("10"),
            max_discount_amount=Decimal("50"),
        )
        # 10% de 100 = 10, sous le cap de 50
        discount = promo.calculate_discount(Decimal("100"))
        assert discount == Decimal("10")

    def test_fixed_inferieur_au_montant(self) -> None:
        promo = _make_promo(type="fixed", value=Decimal("15"))
        discount = promo.calculate_discount(Decimal("100"))
        assert discount == Decimal("15")

    def test_fixed_superieur_au_montant_caponne_au_montant(self) -> None:
        promo = _make_promo(type="fixed", value=Decimal("200"))
        # discount ne peut pas dépasser le montant de la commande
        discount = promo.calculate_discount(Decimal("50"))
        assert discount == Decimal("50")

    @pytest.mark.asyncio
    async def test_validation_code_valide_retourne_discount_correct(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(
            type="percentage",
            value=Decimal("10"),
            starts_at=_now() - timedelta(days=1),
            expires_at=_now() + timedelta(days=30),
            usage_limit=100,
            usage_count=5,
        )

        uc = ValidatePromotionUseCase(repo)
        result = await uc.execute(
            code="PROMO10", amount=Decimal("200"), applicable_to="all"
        )

        assert result.valid is True
        assert result.discount_amount == Decimal("20")  # 10% de 200

    @pytest.mark.asyncio
    async def test_validation_applicable_to_all_accepte_tout(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_promo(applicable_to="all")

        uc = ValidatePromotionUseCase(repo)
        for context in ["products", "services", "appointments"]:
            result = await uc.execute(
                code="PROMO10", amount=Decimal("100"), applicable_to=context
            )
            assert result.valid is True
