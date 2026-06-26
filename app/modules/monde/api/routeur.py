"""Routeur FastAPI du module world — pays, états et villes."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.monde.api.schemas import CitySchema, CountrySchema, StateSchema
from app.modules.monde.application.cas_utilisation import (
    GetCountryUseCase,
    ListCitiesUseCase,
    ListCountriesUseCase,
    ListCountryStatesUseCase,
    ListStateCitiesUseCase,
)
from app.modules.monde.domain.exceptions import CountryNotFoundError, StateNotFoundError
from app.modules.monde.infrastructure.depots import (
    SQLAlchemyCityRepository,
    SQLAlchemyCountryRepository,
    SQLAlchemyStateRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Monde"])

# ---------------------------------------------------------------------------
# Dépendances d'injection
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


@router.get("/pays", response_model=Page[CountrySchema])
async def list_countries(
    search: Annotated[str | None, Query(description="Filtre sur le nom")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> Page[CountrySchema]:
    """Liste paginée des pays avec filtre optionnel par nom."""
    params = PaginationParams(page=page, per_page=per_page)
    # TODO: injecter redis via Depends(get_redis) quand l'Agent 1 expose la dépendance Redis
    uc = ListCountriesUseCase(repo, redis=None)
    resultat = await uc.execute(params, search)
    return resultat  # type: ignore[return-valeur]


@router.get("/pays/{id_pays}", response_model=CountrySchema)
async def get_country(
    id_pays: int,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> CountrySchema:
    """Détail d'un pays."""
    uc = GetCountryUseCase(repo)
    try:
        pays = await uc.execute(id_pays)
    except (CountryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CountrySchema.model_validate(pays)


@router.get("/pays/{id_pays}/etats", response_model=list[StateSchema])
async def list_country_states(
    id_pays: int,
    repo: SQLAlchemyCountryRepository = Depends(_country_repo),
) -> list[StateSchema]:
    """Liste des états/régions d'un pays."""
    uc = ListCountryStatesUseCase(repo)
    try:
        etats = await uc.execute(id_pays)
    except (CountryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [StateSchema.model_validate(e) for e in etats]


@router.get("/etats/{id_region}/villes", response_model=list[CitySchema])
async def list_state_cities(
    id_region: int,
    repo: SQLAlchemyStateRepository = Depends(_state_repo),
) -> list[CitySchema]:
    """Liste des villes d'un état."""
    uc = ListStateCitiesUseCase(repo)
    try:
        villes = await uc.execute(id_region)
    except (StateNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [CitySchema.model_validate(v) for v in villes]


@router.get("/villes", response_model=Page[CitySchema])
async def list_cities(
    id_region: Annotated[int | None, Query(description="Filtre par état")] = None,
    search: Annotated[str | None, Query(description="Filtre sur le nom")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyCityRepository = Depends(_city_repo),
) -> Page[CitySchema]:
    """Liste paginée des villes."""
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListCitiesUseCase(repo)
    resultat = await uc.execute(params, id_region, search)
    return resultat  # type: ignore[return-valeur]
