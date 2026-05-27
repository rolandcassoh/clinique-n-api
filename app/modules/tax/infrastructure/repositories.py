from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.tax.domain.entities import Tax
from app.modules.tax.domain.repositories import AbstractTaxRepository
from app.modules.tax.infrastructure.models import TaxModel


def _to_entity(m: TaxModel) -> Tax:
    return Tax(
        id=m.id,
        name=m.name,
        rate=m.rate,
        type=m.type,
        country_id=m.country_id,
        is_default=m.is_default,
        is_active=m.is_active,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


class SQLTaxRepository(AbstractTaxRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Tax]:
        stmt = select(TaxModel).where(
            TaxModel.deleted_at.is_(None),
            TaxModel.is_active.is_(True),
        ).order_by(TaxModel.name)
        result = await self._session.execute(stmt)
        return [_to_entity(m) for m in result.scalars().all()]

    async def get_default(self) -> Tax | None:
        stmt = select(TaxModel).where(
            TaxModel.deleted_at.is_(None),
            TaxModel.is_active.is_(True),
            TaxModel.is_default.is_(True),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def get_by_id(self, tax_id: int) -> Tax | None:
        stmt = select(TaxModel).where(TaxModel.id == tax_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None,
        is_default: bool,
        is_active: bool,
    ) -> Tax:
        m = TaxModel(
            name=name,
            rate=rate,
            type=type,
            country_id=country_id,
            is_default=is_default,
            is_active=is_active,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(
        self,
        tax_id: int,
        name: str,
        rate: Decimal,
        type: str,
        country_id: int | None,
        is_default: bool,
        is_active: bool,
    ) -> Tax | None:
        stmt = (
            update(TaxModel)
            .where(TaxModel.id == tax_id, TaxModel.deleted_at.is_(None))
            .values(
                name=name,
                rate=rate,
                type=type,
                country_id=country_id,
                is_default=is_default,
                is_active=is_active,
            )
            .returning(TaxModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def set_default(self, tax_id: int) -> Tax:
        """
        Opération atomique : reset toutes les taxes puis set la cible.
        La session parent gère la transaction (via get_db).
        """
        # 1. Reset is_default sur toutes les taxes non supprimées
        reset_stmt = (
            update(TaxModel)
            .where(TaxModel.deleted_at.is_(None))
            .values(is_default=False)
        )
        await self._session.execute(reset_stmt)

        # 2. Set is_default=true sur la taxe cible
        set_stmt = (
            update(TaxModel)
            .where(TaxModel.id == tax_id, TaxModel.deleted_at.is_(None))
            .values(is_default=True)
            .returning(TaxModel)
        )
        result = await self._session.execute(set_stmt)
        m = result.scalar_one()
        return _to_entity(m)

    async def soft_delete(self, tax_id: int) -> bool:
        stmt = (
            update(TaxModel)
            .where(TaxModel.id == tax_id, TaxModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
