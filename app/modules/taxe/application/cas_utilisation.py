"""Cas d'utilisation du module tax."""
from decimal import Decimal

from app.modules.taxe.domain.entites import Tax
from app.modules.taxe.domain.exceptions import NoDefaultTaxError, TaxNotFoundError
from app.modules.taxe.domain.depots import AbstractTaxRepository


class ListActiveTaxesUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Tax]:
        """Retourne toutes les taxes actives."""
        return await self._repo.list_active()


class GetDefaultTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self) -> Tax:
        """Retourne la taxe par défaut ou lève NoDefaultTaxError."""
        taxe = await self._repo.get_default()
        if taxe is None:
            raise NoDefaultTaxError()
        return taxe


class GetTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, id_taxe: int) -> Tax:
        """Retourne une taxe par identifiant ou lève TaxNotFoundError."""
        taxe = await self._repo.get_by_id(id_taxe)
        if taxe is None or taxe.is_deleted:
            raise TaxNotFoundError(id_taxe)
        return taxe


class CreateTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        nom: str,
        tarif: Decimal,
        type: str,
        id_pays: int | None = None,
        est_defaut: bool = False,
        est_actif: bool = True,
    ) -> Tax:
        """Crée une nouvelle taxe."""
        return await self._repo.create(
            nom=nom,
            tarif=tarif,
            type=type,
            id_pays=id_pays,
            est_defaut=est_defaut,
            est_actif=est_actif,
        )


class UpdateTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_taxe: int,
        nom: str,
        tarif: Decimal,
        type: str,
        id_pays: int | None = None,
        est_defaut: bool = False,
        est_actif: bool = True,
    ) -> Tax:
        """Met à jour une taxe existante."""
        mis_a_jour = await self._repo.update(
            id_taxe=id_taxe,
            nom=nom,
            tarif=tarif,
            type=type,
            id_pays=id_pays,
            est_defaut=est_defaut,
            est_actif=est_actif,
        )
        if mis_a_jour is None:
            raise TaxNotFoundError(id_taxe)
        return mis_a_jour


class SetDefaultTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, id_taxe: int) -> Tax:
        """Définit une taxe comme taxe par défaut (opération atomique)."""
        # Vérifier l'existence avant de modifier
        existante = await self._repo.get_by_id(id_taxe)
        if existante is None or existante.is_deleted:
            raise TaxNotFoundError(id_taxe)
        return await self._repo.set_default(id_taxe)


class DeleteTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, id_taxe: int) -> None:
        """Supprime doucement une taxe."""
        supprime = await self._repo.soft_delete(id_taxe)
        if not supprime:
            raise TaxNotFoundError(id_taxe)
