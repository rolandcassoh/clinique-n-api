"""Router FastAPI du module world."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.world.api.schemas import CitySchema, CountrySchema, StateSchema
from app.modules.world.application.use_cases import (
    GetCountryUseCase,
    ListCitiesUseCase,
    ListCountriesUseCase,
    ListCountryStatesUseCase,
    ListStateCitiesUseCase,
)
from app.modules.world.domain.exceptions import CountryNotFoundError, StateNotFoundError
from app.modules.world.infrastructure.repositories import (
    SQLAlchemyCityRepository,
    SQLAlchemyCountryRepository,
    SQLAlchemyStateRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["World"])

# ---------------------------------------------------------------------------
# Dépendances
# ---------------------------------------------------------------------------

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _country_repo(db: DbDep) -> SQLAlchemyCountryRepository:
    return SQLAlchemyCountryRepository(db)


def _state_repo(db: DbDep) -> SQLAlchemyStateRepository:
    return SQLAlchemyStateRepository(db)


def _city_repo(db: DbDep) -> SQLAlchemyCityRepository:
    return SQLAlchemyCityRepository(db)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/countries", response_model=Page[CountrySchema])
async def list_countries(
    search: Annotated[str | None, Query(description="Filtre sur le nom")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> Page[CountrySchema]:
    """Liste paginée des pays avec filtre optionnel par nom."""
    params = PaginationParams(page=page, per_page=per_page)
    # TODO: injecter redis via Depends(get_redis) quand l'Agent 1 expose la dépendance
    uc = ListCountriesUseCase(repo, redis=None)
    result = await uc.execute(params, search)
    return result  # type: ignore[return-value]


@router.get("/countries/{country_id}", response_model=CountrySchema)
async def get_country(
    country_id: int,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> CountrySchema:
    """Détail d'un pays."""
    uc = GetCountryUseCase(repo)
    try:
        country = await uc.execute(country_id)
    except (CountryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CountrySchema.model_validate(country)


@router.get("/countries/{country_id}/states", response_model=list[StateSchema])
async def list_country_states(
    country_id: int,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> list[StateSchema]:
    """Liste des états/régions d'un pays."""
    uc = ListCountryStatesUseCase(repo)
    try:
        states = await uc.execute(country_id)
    except (CountryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [StateSchema.model_validate(s) for s in states]


@router.get("/states/{state_id}/cities", response_model=list[CitySchema])
async def list_state_cities(
    state_id: int,
    repo: SQLAlchemyStateRepository = Depends(_state_repo),
) -> list[CitySchema]:
    """Liste des villes d'un état."""
    uc = ListStateCitiesUseCase(repo)
    try:
        cities = await uc.execute(state_id)
    except (StateNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [CitySchema.model_validate(c) for c in cities]


@router.get("/cities", response_model=Page[CitySchema])
async def list_cities(
    state_id: Annotated[int | None, Query(description="Filtre par état")] = None,
    search: Annotated[str | None, Query(description="Filtre sur le nom")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyCityRepository = Depends(_city_repo),
) -> Page[CitySchema]:
    """Liste paginée des villes."""
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListCitiesUseCase(repo)
    result = await uc.execute(params, state_id, search)
    return result  # type: ignore[return-value]
