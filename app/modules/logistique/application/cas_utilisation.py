"""Use Cases du module Logistic."""
from __future__ import annotations

from decimal import Decimal

from app.modules.logistique.domain.entites import (
    ShippingCalculationResult,
    ShippingRate,
    ShippingZone,
)
from app.modules.logistique.domain.exceptions import (
    NoApplicableShippingRateError,
    ShippingRateNotFoundError,
    ShippingZoneNotFoundError,
)
from app.modules.logistique.domain.depots import ShippingRateRepository, ShippingZoneRepository


class ListActiveZonesUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[ShippingZone]:
        return await self._repo.list_active()


class CreateZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(
        self, nom: str, description: str | None = None, est_actif: bool = True
    ) -> ShippingZone:
        return await self._repo.create(nom=nom, description=description, est_actif=est_actif)


class UpdateZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_zone: int,
        nom: str | None = None,
        description: str | None = None,
        est_actif: bool | None = None,
    ) -> ShippingZone:
        zone = await self._repo.update(
            id_zone=id_zone, nom=nom, description=description, est_actif=est_actif
        )
        if zone is None:
            raise ShippingZoneNotFoundError(id_zone)
        return zone


class DeleteZoneUseCase:
    def __init__(self, repo: ShippingZoneRepository) -> None:
        self._repo = repo

    async def execute(self, id_zone: int) -> None:
        deleted = await self._repo.soft_delete(id_zone)
        if not deleted:
            raise ShippingZoneNotFoundError(id_zone)


class ListRatesUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self, id_zone: int, montant: Decimal | None = None
    ) -> list[ShippingRate]:
        return await self._repo.list_by_zone(id_zone, min_amount=montant)


class CreateRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_zone: int,
        nom: str,
        tarif: Decimal,
        poids_min: Decimal = Decimal("0"),
        poids_max: Decimal | None = None,
        montant_min_commande: Decimal = Decimal("0"),
        livraison_gratuite: bool = False,
        jours_livraison_min: int = 1,
        jours_livraison_max: int = 3,
        est_actif: bool = True,
    ) -> ShippingRate:
        return await self._repo.create(
            id_zone=id_zone, nom=nom, poids_min=poids_min, poids_max=poids_max,
            montant_min_commande=montant_min_commande, tarif=tarif, livraison_gratuite=livraison_gratuite,
            jours_livraison_min=jours_livraison_min, jours_livraison_max=jours_livraison_max,
            est_actif=est_actif,
        )


class UpdateRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        rate_id: int,
        nom: str | None = None,
        poids_min: Decimal | None = None,
        poids_max: Decimal | None = None,
        montant_min_commande: Decimal | None = None,
        tarif: Decimal | None = None,
        livraison_gratuite: bool | None = None,
        jours_livraison_min: int | None = None,
        jours_livraison_max: int | None = None,
        est_actif: bool | None = None,
    ) -> ShippingRate:
        result = await self._repo.update(
            rate_id=rate_id, nom=nom, poids_min=poids_min, poids_max=poids_max,
            montant_min_commande=montant_min_commande, tarif=tarif, livraison_gratuite=livraison_gratuite,
            jours_livraison_min=jours_livraison_min, jours_livraison_max=jours_livraison_max,
            est_actif=est_actif,
        )
        if result is None:
            raise ShippingRateNotFoundError(rate_id)
        return result


class DeleteRateUseCase:
    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(self, rate_id: int) -> None:
        deleted = await self._repo.soft_delete(rate_id)
        if not deleted:
            raise ShippingRateNotFoundError(rate_id)


class CalculateShippingUseCase:
    """
    Algorithme de calcul de livraison :
    1. Filtrer les tarifs actifs de la zone
    2. Garder ceux où montant_min_commande <= montant
    3. Si livraison_gratuite=true → retourner {taux: 0, estimated_days: ...}
    4. Sinon → retourner le tarif le moins cher applicable
    """

    def __init__(self, repo: ShippingRateRepository) -> None:
        self._repo = repo

    async def execute(self, id_zone: int, montant: Decimal) -> ShippingCalculationResult:
        tarifs = await self._repo.list_by_zone(id_zone, min_amount=montant)

        if not tarifs:
            raise NoApplicableShippingRateError(id_zone, float(montant))

        # Priorité au tarif gratuit
        for t in tarifs:
            if t.livraison_gratuite:
                return ShippingCalculationResult(
                    tarif=Decimal("0"),
                    jours_livraison_min=t.jours_livraison_min,
                    jours_livraison_max=t.jours_livraison_max,
                    rate_name=t.nom,
                    livraison_gratuite=True,
                )

        # Sinon, le tarif le moins cher
        moins_cher = min(tarifs, cle=lambda t: t.tarif)
        return ShippingCalculationResult(
            tarif=moins_cher.tarif,
            jours_livraison_min=moins_cher.jours_livraison_min,
            jours_livraison_max=moins_cher.jours_livraison_max,
            rate_name=moins_cher.nom,
            livraison_gratuite=False,
        )
