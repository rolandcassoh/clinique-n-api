from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.currency.domain.entities import Currency
from app.modules.currency.domain.repositories import AbstractCurrencyRepository
from app.modules.currency.infrastructure.models import CurrencyModel


def _to_entity(m: CurrencyModel) -> Currency:
    return Currency(
        id=m.id, name=m.name, code=m.code, symbol=m.symbol,
        exchange_rate=m.exchange_rate, is_default=m.is_default, is_active=m.is_active,
    )


class SQLCurrencyRepository(AbstractCurrencyRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Currency]:
        stmt = select(CurrencyModel).where(
            CurrencyModel.is_active.is_(True),
            CurrencyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_to_entity(row) for row in result.scalars().all()]

    async def get_default(self) -> Currency | None:
        stmt = select(CurrencyModel).where(
            CurrencyModel.is_default.is_(True),
            CurrencyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_code(self, code: str) -> Currency | None:
        stmt = select(CurrencyModel).where(
            CurrencyModel.code == code,
            CurrencyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_id(self, currency_id: int) -> Currency | None:
        stmt = select(CurrencyModel).where(
            CurrencyModel.id == currency_id,
            CurrencyModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self, name: str, code: str, symbol: str, exchange_rate: Decimal,
        is_default: bool, is_active: bool
    ) -> Currency:
        m = CurrencyModel(
            name=name, code=code, symbol=symbol,
            exchange_rate=exchange_rate, is_default=is_default, is_active=is_active,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(
        self, currency_id: int, name: str, code: str, symbol: str,
        exchange_rate: Decimal, is_default: bool, is_active: bool
    ) -> Currency | None:
        stmt = (
            update(CurrencyModel)
            .where(CurrencyModel.id == currency_id, CurrencyModel.deleted_at.is_(None))
            .values(
                name=name, code=code, symbol=symbol,
                exchange_rate=exchange_rate, is_default=is_default, is_active=is_active,
            )
            .returning(CurrencyModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def set_default(self, currency_id: int) -> Currency | None:
        # Vérifier que la devise existe avant de toucher les autres
        target = await self.get_by_id(currency_id)
        if target is None:
            return None

        # Reset toutes les devises dans la même transaction
        await self._session.execute(
            update(CurrencyModel)
            .where(CurrencyModel.deleted_at.is_(None))
            .values(is_default=False)
        )
        stmt = (
            update(CurrencyModel)
            .where(CurrencyModel.id == currency_id)
            .values(is_default=True)
            .returning(CurrencyModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None
