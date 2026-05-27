"""Use Cases du module world."""
import json
from typing import Any

from app.modules.world.domain.entities import City, Country, State
from app.modules.world.domain.exceptions import CountryNotFoundError, StateNotFoundError
from app.modules.world.domain.repositories import (
    CityRepository,
    CountryRepository,
    StateRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

# TODO: injecter get_redis depuis app.core.cache.redis_client quand disponible
_COUNTRY_LIST_CACHE_KEY = "world:countries:list"
_COUNTRY_LIST_TTL = 3600  # 1 heure


class ListCountriesUseCase:
    def __init__(self, repo: CountryRepository, redis: Any | None = None) -> None:
        self._repo = repo
        self._redis = redis

    async def execute(
        self, params: PaginationParams, search: str | None = None
    ) -> Page[Country]:
        # Cache Redis uniquement sur la liste non filtrée (données très stables)
        cache_key = f"{_COUNTRY_LIST_CACHE_KEY}:p{params.page}:pp{params.per_page}"
        if self._redis is not None and search is None:
            cached = await self._redis.get(cache_key)
            if cached:
                raw = json.loads(cached)
                # On retourne directement le dict sérialisé
                return raw  # type: ignore[return-value]

        countries, total = await self._repo.list(params, search)
        page: Page[Country] = Page.create(data=countries, total=total, params=params)

        if self._redis is not None and search is None:
            await self._redis.setex(cache_key, _COUNTRY_LIST_TTL, json.dumps(page, default=str))

        return page


class GetCountryUseCase:
    def __init__(self, repo: CountryRepository) -> None:
        self._repo = repo

    async def execute(self, country_id: int) -> Country:
        country = await self._repo.get_by_id(country_id)
        if country is None:
            raise CountryNotFoundError(country_id)
        return country


class ListCountryStatesUseCase:
    def __init__(self, country_repo: CountryRepository) -> None:
        self._repo = country_repo

    async def execute(self, country_id: int) -> list[State]:
        country = await self._repo.get_by_id(country_id)
        if country is None:
            raise CountryNotFoundError(country_id)
        return await self._repo.list_states(country_id)


class ListStateCitiesUseCase:
    def __init__(self, state_repo: StateRepository) -> None:
        self._repo = state_repo

    async def execute(self, state_id: int) -> list[City]:
        state = await self._repo.get_by_id(state_id)
        if state is None:
            raise StateNotFoundError(state_id)
        return await self._repo.list_cities(state_id)


class ListCitiesUseCase:
    def __init__(self, repo: CityRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        state_id: int | None = None,
        search: str | None = None,
    ) -> Page[City]:
        cities, total = await self._repo.list(params, state_id, search)
        return Page.create(data=cities, total=total, params=params)
