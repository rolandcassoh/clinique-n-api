"""Cas d'utilisation du module world."""
import json
from typing import Any

from app.modules.monde.domain.entites import City, Country, State
from app.modules.monde.domain.exceptions import CountryNotFoundError, StateNotFoundError
from app.modules.monde.domain.depots import (
    CityRepository,
    CountryRepository,
    StateRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

# TODO: injecter get_redis depuis app.core.cache.redis_client quand disponible
_COUNTRY_LIST_CACHE_KEY = "world:countries:list"
_COUNTRY_LIST_TTL = 3600  # 1 heure (données géographiques très stables)


class ListCountriesUseCase:
    def __init__(self, repo: CountryRepository, redis: Any | None = None) -> None:
        self._repo = repo
        self._redis = redis

    async def execute(
        self, params: PaginationParams, search: str | None = None
    ) -> Page[Country]:
        # Mise en cache Redis uniquement sur la liste non filtrée (données très stables)
        cle_cache = f"{_COUNTRY_LIST_CACHE_KEY}:p{params.page}:pp{params.per_page}"
        if self._redis is not None and search is None:
            cache = await self._redis.get(cle_cache)
            if cache:
                donnees_brutes = json.loads(cache)
                # Retourne directement le dictionnaire sérialisé
                return donnees_brutes  # type: ignore[return-valeur]

        pays, total = await self._repo.list(params, search)
        page: Page[Country] = Page.create(data=pays, total=total, params=params)

        if self._redis is not None and search is None:
            await self._redis.setex(cle_cache, _COUNTRY_LIST_TTL, json.dumps(page, default=str))

        return page


class GetCountryUseCase:
    def __init__(self, repo: CountryRepository) -> None:
        self._repo = repo

    async def execute(self, id_pays: int) -> Country:
        pays = await self._repo.get_by_id(id_pays)
        if pays is None:
            raise CountryNotFoundError(id_pays)
        return pays


class ListCountryStatesUseCase:
    def __init__(self, country_repo: CountryRepository) -> None:
        self._repo = country_repo

    async def execute(self, id_pays: int) -> list[State]:
        pays = await self._repo.get_by_id(id_pays)
        if pays is None:
            raise CountryNotFoundError(id_pays)
        return await self._repo.list_states(id_pays)


class ListStateCitiesUseCase:
    def __init__(self, state_repo: StateRepository) -> None:
        self._repo = state_repo

    async def execute(self, id_region: int) -> list[City]:
        etat = await self._repo.get_by_id(id_region)
        if etat is None:
            raise StateNotFoundError(id_region)
        return await self._repo.list_cities(id_region)


class ListCitiesUseCase:
    def __init__(self, repo: CityRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_region: int | None = None,
        search: str | None = None,
    ) -> Page[City]:
        villes, total = await self._repo.list(params, id_region, search)
        return Page.create(data=villes, total=total, params=params)
