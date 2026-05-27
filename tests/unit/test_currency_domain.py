"""Tests unitaires — domaine Currency (logique pure, sans I/O)."""
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.modules.currency.application.use_cases import CurrencyUseCases
from app.modules.currency.domain.entities import Currency
from app.modules.currency.domain.exceptions import CurrencyCodeConflictError, CurrencyNotFoundError


def _make_currency(id: int = 1, code: str = "XAF", is_default: bool = False) -> Currency:
    return Currency(
        id=id, name="Franc CFA", code=code, symbol="FCFA",
        exchange_rate=Decimal("1.0"), is_default=is_default, is_active=True,
    )


class TestCurrencyEntity:
    def test_set_default_marks_currency(self) -> None:
        currency = _make_currency(is_default=False)
        currency.set_default()
        assert currency.is_default is True

    def test_unset_default_unmarks_currency(self) -> None:
        currency = _make_currency(is_default=True)
        currency.unset_default()
        assert currency.is_default is False


class TestCurrencyCodeUppercase:
    @pytest.mark.asyncio
    async def test_create_uppercases_code(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = None
        created = _make_currency(code="XAF")
        repo.create.return_value = created
        uc = CurrencyUseCases(repo)

        await uc.create_currency(
            name="Franc CFA", code="xaf", symbol="FCFA",
            exchange_rate=Decimal("1"), is_default=False, is_active=True,
        )

        # Vérifie que le code transmis au repo est en majuscules
        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["code"] == "XAF"

    @pytest.mark.asyncio
    async def test_get_by_code_uppercases_lookup(self) -> None:
        repo = AsyncMock()
        currency = _make_currency(code="EUR")
        repo.get_by_code.return_value = currency
        uc = CurrencyUseCases(repo)

        result = await uc.get_by_code("eur")

        repo.get_by_code.assert_awaited_once_with("EUR")
        assert result.code == "EUR"


class TestCurrencySetDefault:
    @pytest.mark.asyncio
    async def test_set_default_raises_not_found(self) -> None:
        repo = AsyncMock()
        repo.set_default.return_value = None
        uc = CurrencyUseCases(repo)

        with pytest.raises(CurrencyNotFoundError):
            await uc.set_default(999)

    @pytest.mark.asyncio
    async def test_set_default_returns_updated_currency(self) -> None:
        repo = AsyncMock()
        currency = _make_currency(is_default=True)
        repo.set_default.return_value = currency
        uc = CurrencyUseCases(repo)

        result = await uc.set_default(1)

        assert result.is_default is True
        repo.set_default.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_create_raises_conflict_on_duplicate_code(self) -> None:
        repo = AsyncMock()
        repo.get_by_code.return_value = _make_currency(code="USD")
        uc = CurrencyUseCases(repo)

        with pytest.raises(CurrencyCodeConflictError):
            await uc.create_currency(
                name="Dollar", code="USD", symbol="$",
                exchange_rate=Decimal("600"), is_default=False, is_active=True,
            )
