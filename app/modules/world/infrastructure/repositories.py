"""Implémentations SQLAlchemy async des repositories world."""
from __future__ import annotations  # évite le shadow de list[] par la méthode list()

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.world.domain.entities import City, Country, State
from app.modules.world.domain.repositories import (
    CityRepository,
    CountryRepository,
    StateRepository,
)
from app.modules.world.infrastructure.models import CityModel, CountryModel, StateModel
from app.shared.schemas.pagination import PaginationParams


def _country_to_entity(m: CountryModel) -> Country:
    return Country(
        id=m.id,
        name=m.name,
        iso2=m.iso2,
        iso3=m.iso3,
        phone_code=m.phone_code,
        capital=m.capital,
        currency=m.currency,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _state_to_entity(m: StateModel) -> State:
    return State(
        id=m.id,
        country_id=m.country_id,
        name=m.name,
        state_code=m.state_code,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _city_to_entity(m: CityModel) -> City:
    return City(
        id=m.id,
        state_id=m.state_id,
        name=m.name,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyCountryRepository(CountryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, params: PaginationParams, search: str | None = None
    ) -> tuple[list[Country], int]:
        base_q = select(CountryModel).where(CountryModel.deleted_at.is_(None))
        if search:
            base_q = base_q.where(CountryModel.name.ilike(f"%{search}%"))

        count_q = select(func.count()).select_from(base_q.subquery())
        total_result = await self._session.execute(count_q)
        total: int = total_result.scalar_one()

        rows_q = base_q.order_by(CountryModel.name).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(rows_q)
        rows = result.scalars().all()

        return [_country_to_entity(r) for r in rows], total

    async def get_by_id(self, country_id: int) -> Country | None:
        q = select(CountryModel).where(
            CountryModel.id == country_id,
            CountryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(q)
        row = result.scalar_one_or_none()
        return _country_to_entity(row) if row else None

    async def list_states(self, country_id: int) -> list[State]:
        q = (
            select(StateModel)
            .where(
                StateModel.country_id == country_id,
                StateModel.deleted_at.is_(None),
            )
            .order_by(StateModel.name)
        )
        result = await self._session.execute(q)
        rows = result.scalars().all()
        return [_state_to_entity(r) for r in rows]


class SQLAlchemyStateRepository(StateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, state_id: int) -> State | None:
        q = select(StateModel).where(
            StateModel.id == state_id,
            StateModel.deleted_at.is_(None),
        )
        result = await self._session.execute(q)
        row = result.scalar_one_or_none()
        return _state_to_entity(row) if row else None

    async def list_cities(self, state_id: int) -> list[City]:
        q = (
            select(CityModel)
            .where(
                CityModel.state_id == state_id,
                CityModel.deleted_at.is_(None),
            )
            .order_by(CityModel.name)
        )
        result = await self._session.execute(q)
        rows = result.scalars().all()
        return [_city_to_entity(r) for r in rows]


class SQLAlchemyCityRepository(CityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        params: PaginationParams,
        state_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[City], int]:
        base_q = select(CityModel).where(CityModel.deleted_at.is_(None))
        if state_id is not None:
            base_q = base_q.where(CityModel.state_id == state_id)
        if search:
            base_q = base_q.where(CityModel.name.ilike(f"%{search}%"))

        count_q = select(func.count()).select_from(base_q.subquery())
        total_result = await self._session.execute(count_q)
        total: int = total_result.scalar_one()

        rows_q = base_q.order_by(CityModel.name).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(rows_q)
        rows = result.scalars().all()

        return [_city_to_entity(r) for r in rows], total
