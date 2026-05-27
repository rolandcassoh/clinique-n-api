from decimal import Decimal

from app.modules.tax.domain.entities import Tax
from app.modules.tax.domain.exceptions import NoDefaultTaxError, TaxNotFoundError
from app.modules.tax.domain.repositories import AbstractTaxRepository


class ListActiveTaxesUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[Tax]:
        return await self._repo.list_active()


class GetDefaultTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self) -> Tax:
        tax = await self._repo.get_default()
        if tax is None:
            raise NoDefaultTaxError()
        return tax


class GetTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, tax_id: int) -> Tax:
        tax = await self._repo.get_by_id(tax_id)
        if tax is None or tax.is_deleted:
            raise TaxNotFoundError(tax_id)
        return tax


class CreateTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None = None,
        is_default: bool = False,
        is_active: bool = True,
    ) -> Tax:
        return await self._repo.create(
            name=name,
            rate=rate,
            type=type,
            country_id=country_id,
            is_default=is_default,
            is_active=is_active,
        )


class UpdateTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        tax_id: int,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None = None,
        is_default: bool = False,
        is_active: bool = True,
    ) -> Tax:
        updated = await self._repo.update(
            tax_id=tax_id,
            name=name,
            rate=rate,
            type=type,
            country_id=country_id,
            is_default=is_default,
            is_active=is_active,
        )
        if updated is None:
            raise TaxNotFoundError(tax_id)
        return updated


class SetDefaultTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, tax_id: int) -> Tax:
        # Vérifier existence d'abord
        existing = await self._repo.get_by_id(tax_id)
        if existing is None or existing.is_deleted:
            raise TaxNotFoundError(tax_id)
        return await self._repo.set_default(tax_id)


class DeleteTaxUseCase:
    def __init__(self, repo: AbstractTaxRepository) -> None:
        self._repo = repo

    async def execute(self, tax_id: int) -> None:
        deleted = await self._repo.soft_delete(tax_id)
        if not deleted:
            raise TaxNotFoundError(tax_id)
