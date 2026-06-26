"""Implémentations SQLAlchemy asynchrones des repositories world."""
from __future__ import annotations  # évite le conflit entre list[] builtin et la méthode list()

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.monde.domain.entites import City, Country, State
from app.modules.monde.domain.depots import (
    CityRepository,
    CountryRepository,
    StateRepository,
)
from app.modules.monde.infrastructure.modeles import CityModel, CountryModel, StateModel
from app.shared.schemas.pagination import PaginationParams


def _country_to_entity(m: CountryModel) -> Country:
    return Country(
        id=m.id,
        nom=m.nom,
        code_iso2=m.code_iso2,
        code_iso3=m.code_iso3,
        indicatif_telephone=m.indicatif_telephone,
        capitale=m.capitale,
        devise=m.devise,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _state_to_entity(m: StateModel) -> State:
    return State(
        id=m.id,
        id_pays=m.id_pays,
        nom=m.nom,
        code_region=m.code_region,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _city_to_entity(m: CityModel) -> City:
    return City(
        id=m.id,
        id_region=m.id_region,
        nom=m.nom,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyCountryRepository(CountryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self, params: PaginationParams, search: str | None = None
    ) -> tuple[list[Country], int]:
        requete_base = select(CountryModel).where(CountryModel.deleted_at.is_(None))
        if search:
            requete_base = requete_base.where(CountryModel.nom.ilike(f"%{search}%"))

        requete_compte = select(func.count()).select_from(requete_base.subquery())
        resultat_total = await self._session.execute(requete_compte)
        total: int = resultat_total.scalar_one()

        requete_lignes = requete_base.order_by(CountryModel.nom).offset(params.offset).limit(params.per_page)
        resultat = await self._session.execute(requete_lignes)
        lignes = resultat.scalars().all()

        return [_country_to_entity(r) for r in lignes], total

    async def get_by_id(self, id_pays: int) -> Country | None:
        requete = select(CountryModel).where(
            CountryModel.id == id_pays,
            CountryModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        ligne = resultat.scalar_one_or_none()
        return _country_to_entity(ligne) if ligne else None

    async def list_states(self, id_pays: int) -> list[State]:
        requete = (
            select(StateModel)
            .where(
                StateModel.id_pays == id_pays,
                StateModel.deleted_at.is_(None),
            )
            .order_by(StateModel.nom)
        )
        resultat = await self._session.execute(requete)
        lignes = resultat.scalars().all()
        return [_state_to_entity(r) for r in lignes]


class SQLAlchemyStateRepository(StateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_region: int) -> State | None:
        requete = select(StateModel).where(
            StateModel.id == id_region,
            StateModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        ligne = resultat.scalar_one_or_none()
        return _state_to_entity(ligne) if ligne else None

    async def list_cities(self, id_region: int) -> list[City]:
        requete = (
            select(CityModel)
            .where(
                CityModel.id_region == id_region,
                CityModel.deleted_at.is_(None),
            )
            .order_by(CityModel.nom)
        )
        resultat = await self._session.execute(requete)
        lignes = resultat.scalars().all()
        return [_city_to_entity(r) for r in lignes]


class SQLAlchemyCityRepository(CityRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        params: PaginationParams,
        id_region: int | None = None,
        search: str | None = None,
    ) -> tuple[list[City], int]:
        requete_base = select(CityModel).where(CityModel.deleted_at.is_(None))
        if id_region is not None:
            requete_base = requete_base.where(CityModel.id_region == id_region)
        if search:
            requete_base = requete_base.where(CityModel.nom.ilike(f"%{search}%"))

        requete_compte = select(func.count()).select_from(requete_base.subquery())
        resultat_total = await self._session.execute(requete_compte)
        total: int = resultat_total.scalar_one()

        requete_lignes = requete_base.order_by(CityModel.nom).offset(params.offset).limit(params.per_page)
        resultat = await self._session.execute(requete_lignes)
        lignes = resultat.scalars().all()

        return [_city_to_entity(r) for r in lignes], total
