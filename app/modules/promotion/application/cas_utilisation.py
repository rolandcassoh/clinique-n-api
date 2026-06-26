"""Cas d'utilisation du module promotion."""
from datetime import datetime, timezone
from decimal import Decimal

from app.modules.promotion.domain.entites import Promotion, PromotionUse, ValidationResult
from app.modules.promotion.domain.exceptions import (
    PromotionCodeConflictError,
    PromotionNotFoundError,
)
from app.modules.promotion.domain.depots import AbstractPromotionRepository
from app.shared.schemas.pagination import Page, PaginationParams


class ValidatePromotionUseCase:
    """
    Valide un code promo selon les règles métier :
    1. Code existe et est_actif = true
    2. Date actuelle entre debut_le et expire_le (si définis)
    3. compteur_utilisation < limite_utilisation (si limite_utilisation défini)
    4. montant >= montant_min_commande (si défini)
    5. applicable_a correspond au contexte
    6. Calcule le montant_remise
    """

    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        code: str,
        montant: Decimal,
        applicable_a: str,
    ) -> ValidationResult:
        promotion_obj = await self._repo.get_by_code(code)

        if promotion_obj is None or not promotion_obj.est_actif or promotion_obj.is_deleted:
            return ValidationResult(
                valid=False,
                montant_remise=Decimal("0"),
                promotion=None,
                motif="Code invalide ou inactif",
            )

        maintenant = datetime.now(timezone.utc)

        if not promotion_obj.is_valid_at(maintenant):
            return ValidationResult(
                valid=False,
                montant_remise=Decimal("0"),
                promotion=promotion_obj,
                motif="Code expiré ou pas encore actif",
            )

        if not promotion_obj.has_remaining_uses():
            return ValidationResult(
                valid=False,
                montant_remise=Decimal("0"),
                promotion=promotion_obj,
                motif="Limite d'utilisation atteinte",
            )

        if promotion_obj.montant_min_commande is not None and montant < promotion_obj.montant_min_commande:
            return ValidationResult(
                valid=False,
                montant_remise=Decimal("0"),
                promotion=promotion_obj,
                motif=f"Montant minimum requis : {promotion_obj.montant_min_commande}",
            )

        if not promotion_obj.is_applicable_to(applicable_a):
            return ValidationResult(
                valid=False,
                montant_remise=Decimal("0"),
                promotion=promotion_obj,
                motif=f"Code non applicable à '{applicable_a}'",
            )

        remise = promotion_obj.calculate_discount(montant)

        return ValidationResult(
            valid=True,
            montant_remise=remise,
            promotion=promotion_obj,
        )


class ListPromotionsUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[Promotion]:
        return await self._repo.list(params)


class GetPromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, id_promotion: int) -> Promotion:
        promotion_obj = await self._repo.get_by_id(id_promotion)
        if promotion_obj is None or promotion_obj.is_deleted:
            raise PromotionNotFoundError(id_promotion)
        return promotion_obj


class CreatePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        code: str,
        nom: str,
        type: str,
        valeur: Decimal,
        montant_min_commande: Decimal | None = None,
        remise_maximale: Decimal | None = None,
        limite_utilisation: int | None = None,
        debut_le: datetime | None = None,
        expire_le: datetime | None = None,
        est_actif: bool = True,
        applicable_a: str = "all",
    ) -> Promotion:
        existante = await self._repo.get_by_code(code)
        if existante is not None and not existante.is_deleted:
            raise PromotionCodeConflictError(code)
        return await self._repo.create(
            code=code,
            nom=nom,
            type=type,
            valeur=valeur,
            montant_min_commande=montant_min_commande,
            remise_maximale=remise_maximale,
            limite_utilisation=limite_utilisation,
            debut_le=debut_le,
            expire_le=expire_le,
            est_actif=est_actif,
            applicable_a=applicable_a,
        )


class UpdatePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_promotion: int,
        code: str,
        nom: str,
        type: str,
        valeur: Decimal,
        montant_min_commande: Decimal | None = None,
        remise_maximale: Decimal | None = None,
        limite_utilisation: int | None = None,
        debut_le: datetime | None = None,
        expire_le: datetime | None = None,
        est_actif: bool = True,
        applicable_a: str = "all",
    ) -> Promotion:
        # Vérifier le conflit de code avec une autre promotion
        existante = await self._repo.get_by_code(code)
        if existante is not None and existante.id != id_promotion and not existante.is_deleted:
            raise PromotionCodeConflictError(code)

        mise_a_jour = await self._repo.update(
            id_promotion=id_promotion,
            code=code,
            nom=nom,
            type=type,
            valeur=valeur,
            montant_min_commande=montant_min_commande,
            remise_maximale=remise_maximale,
            limite_utilisation=limite_utilisation,
            debut_le=debut_le,
            expire_le=expire_le,
            est_actif=est_actif,
            applicable_a=applicable_a,
        )
        if mise_a_jour is None:
            raise PromotionNotFoundError(id_promotion)
        return mise_a_jour


class DeletePromotionUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(self, id_promotion: int) -> None:
        supprime = await self._repo.soft_delete(id_promotion)
        if not supprime:
            raise PromotionNotFoundError(id_promotion)


class ListPromotionUsesUseCase:
    def __init__(self, repo: AbstractPromotionRepository) -> None:
        self._repo = repo

    async def execute(
        self, id_promotion: int, params: PaginationParams
    ) -> Page[PromotionUse]:
        # Vérifier que la promotion existe avant de lister ses utilisations
        promotion_obj = await self._repo.get_by_id(id_promotion)
        if promotion_obj is None or promotion_obj.is_deleted:
            raise PromotionNotFoundError(id_promotion)
        return await self._repo.list_uses(id_promotion, params)
