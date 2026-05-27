from datetime import datetime, timezone
from decimal import Decimal

from app.modules.promotion.domain.entities import Promotion, PromotionUse, ValidationResult
from app.modules.promotion.domain.exceptions import (
    PromotionCodeConflictError,
    PromotionNotFoundError,
)
from app.modules.promotion.domain.repositories import AbstractPromotionRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ValidatePromotionUseCase:
    """
    Valide un code promo selon les règles métier :
    1. Code existe et is_active = true
    2. Date actuelle entre starts_at et expires_at (si définis)
    3. usage_count < usage_limit (si usage_limit défini)
    4. amount >= min_order_amount (si défini)
    5. applicable_to correspond au contexte
    6. Calcule le discount_amount
    """

    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        code: str,
        amount: Decimal,
        applicable_to: str,
    ) -> ValidationResult:
        promotion = await self._repo.get_by_code(code)

        if promotion is None or not promotion.is_active or promotion.is_deleted:
            return ValidationResult(
                valid=False,
                discount_amount=Decimal("0"),
                promotion=None,
                reason="Code invalide ou inactif",
            )

        now = datetime.now(timezone.utc)

        if not promotion.is_valid_at(now):
            return ValidationResult(
                valid=False,
                discount_amount=Decimal("0"),
                promotion=promotion,
                reason="Code expiré ou pas encore actif",
            )

        if not promotion.has_remaining_uses():
            return ValidationResult(
                valid=False,
                discount_amount=Decimal("0"),
                promotion=promotion,
                reason="Limite d'utilisation atteinte",
            )

        if promotion.min_order_amount is not None and amount < promotion.min_order_amount:
            return ValidationResult(
                valid=False,
                discount_amount=Decimal("0"),
                promotion=promotion,
                reason=f"Montant minimum requis : {promotion.min_order_amount}",
            )

        if not promotion.is_applicable_to(applicable_to):
            return ValidationResult(
                valid=False,
                discount_amount=Decimal("0"),
                promotion=promotion,
                reason=f"Code non applicable à '{applicable_to}'",
            )

        discount = promotion.calculate_discount(amount)

        return ValidationResult(
            valid=True,
            discount_amount=discount,
            promotion=promotion,
        )


class ListPromotionsUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[Promotion]:
        return await self._repo.list(params)


class GetPromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, promotion_id: int) -> Promotion:
        promo = await self._repo.get_by_id(promotion_id)
        if promo is None or promo.is_deleted:
            raise PromotionNotFoundError(promotion_id)
        return promo


class CreatePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        code: str,
        name: str,
        type: str,
        value: Decimal,
        min_order_amount: Decimal | None = None,
        max_discount_amount: Decimal | None = None,
        usage_limit: int | None = None,
        starts_at: datetime | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
        applicable_to: str = "all",
    ) -> Promotion:
        existing = await self._repo.get_by_code(code)
        if existing is not None and not existing.is_deleted:
            raise PromotionCodeConflictError(code)
        return await self._repo.create(
            code=code,
            name=name,
            type=type,
            value=value,
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount,
            usage_limit=usage_limit,
            starts_at=starts_at,
            expires_at=expires_at,
            is_active=is_active,
            applicable_to=applicable_to,
        )


class UpdatePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        promotion_id: int,
        code: str,
        name: str,
        type: str,
        value: Decimal,
        min_order_amount: Decimal | None = None,
        max_discount_amount: Decimal | None = None,
        usage_limit: int | None = None,
        starts_at: datetime | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
        applicable_to: str = "all",
    ) -> Promotion:
        # Vérifier conflit de code avec une autre promo
        existing = await self._repo.get_by_code(code)
        if existing is not None and existing.id != promotion_id and not existing.is_deleted:
            raise PromotionCodeConflictError(code)

        updated = await self._repo.update(
            promotion_id=promotion_id,
            code=code,
            name=name,
            type=type,
            value=value,
            min_order_amount=min_order_amount,
            max_discount_amount=max_discount_amount,
            usage_limit=usage_limit,
            starts_at=starts_at,
            expires_at=expires_at,
            is_active=is_active,
            applicable_to=applicable_to,
        )
        if updated is None:
            raise PromotionNotFoundError(promotion_id)
        return updated


class DeletePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, promotion_id: int) -> None:
        deleted = await self._repo.soft_delete(promotion_id)
        if not deleted:
            raise PromotionNotFoundError(promotion_id)


class ListPromotionUsesUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self, promotion_id: int, params: PaginationParams
    ) -> Page[PromotionUse]:
        # Vérifier que la promo existe
        promo = await self._repo.get_by_id(promotion_id)
        if promo is None or promo.is_deleted:
            raise PromotionNotFoundError(promotion_id)
        return await self._repo.list_uses(promotion_id, params)
