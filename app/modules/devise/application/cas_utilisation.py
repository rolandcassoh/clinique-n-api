"""Cas d'utilisation du module devise (devise)."""
from decimal import Decimal

from app.modules.devise.domain.entites import Currency
from app.modules.devise.domain.exceptions import CurrencyCodeConflictError, CurrencyNotFoundError
from app.modules.devise.domain.depots import AbstractCurrencyRepository


class CurrencyUseCases:
    def __init__(self, repo: AbstractCurrencyRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Currency]:
        return await self._repo.list_active()

    async def get_default(self) -> Currency:
        devise = await self._repo.get_default()
        if devise is None:
            raise CurrencyNotFoundError("default")
        return devise

    async def get_by_code(self, code: str) -> Currency:
        devise = await self._repo.get_by_code(code.upper())
        if devise is None:
            raise CurrencyNotFoundError(code)
        return devise

    async def create_currency(
        self, nom: str, code: str, symbole: str,
        taux_change: Decimal, est_defaut: bool = False, est_actif: bool = True
    ) -> Currency:
        code = code.upper()
        existante = await self._repo.get_by_code(code)
        if existante is not None:
            raise CurrencyCodeConflictError(code)
        return await self._repo.create(
            nom=nom, code=code, symbole=symbole,
            taux_change=taux_change, est_defaut=est_defaut, est_actif=est_actif
        )

    async def update_currency(
        self, currency_id: int, nom: str, code: str, symbole: str,
        taux_change: Decimal, est_defaut: bool, est_actif: bool
    ) -> Currency:
        code = code.upper()
        existante = await self._repo.get_by_code(code)
        if existante is not None and existante.id != currency_id:
            raise CurrencyCodeConflictError(code)
        mise_a_jour = await self._repo.update(
            currency_id, nom=nom, code=code, symbole=symbole,
            taux_change=taux_change, est_defaut=est_defaut, est_actif=est_actif
        )
        if mise_a_jour is None:
            raise CurrencyNotFoundError(currency_id)
        return mise_a_jour

    async def set_default(self, currency_id: int) -> Currency:
        devise = await self._repo.set_default(currency_id)
        if devise is None:
            raise CurrencyNotFoundError(currency_id)
        return devise
