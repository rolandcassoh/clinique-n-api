from decimal import Decimal

from app.modules.currency.domain.entities import Currency
from app.modules.currency.domain.exceptions import CurrencyCodeConflictError, CurrencyNotFoundError
from app.modules.currency.domain.repositories import AbstractCurrencyRepository


class CurrencyUseCases:
    def __init__(self, repo: AbstractCurrencyRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Currency]:
        return await self._repo.list_active()

    async def get_default(self) -> Currency:
        currency = await self._repo.get_default()
        if currency is None:
            raise CurrencyNotFoundError("default")
        return currency

    async def get_by_code(self, code: str) -> Currency:
        currency = await self._repo.get_by_code(code.upper())
        if currency is None:
            raise CurrencyNotFoundError(code)
        return currency

    async def create_currency(
        self, name: str, code: str, symbol: str,
        exchange_rate: Decimal, is_default: bool = False, is_active: bool = True
    ) -> Currency:
        code = code.upper()
        existing = await self._repo.get_by_code(code)
        if existing is not None:
            raise CurrencyCodeConflictError(code)
        return await self._repo.create(
            name=name, code=code, symbol=symbol,
            exchange_rate=exchange_rate, is_default=is_default, is_active=is_active
        )

    async def update_currency(
        self, currency_id: int, name: str, code: str, symbol: str,
        exchange_rate: Decimal, is_default: bool, is_active: bool
    ) -> Currency:
        code = code.upper()
        existing = await self._repo.get_by_code(code)
        if existing is not None and existing.id != currency_id:
            raise CurrencyCodeConflictError(code)
        updated = await self._repo.update(
            currency_id, name=name, code=code, symbol=symbol,
            exchange_rate=exchange_rate, is_default=is_default, is_active=is_active
        )
        if updated is None:
            raise CurrencyNotFoundError(currency_id)
        return updated

    async def set_default(self, currency_id: int) -> Currency:
        currency = await self._repo.set_default(currency_id)
        if currency is None:
            raise CurrencyNotFoundError(currency_id)
        return currency
