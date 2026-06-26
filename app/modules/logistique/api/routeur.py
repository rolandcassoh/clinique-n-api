"""Router FastAPI du module Logistic."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.logistique.api.schemas import (
    ShippingCalculationSchema,
    ShippingRateCreateRequest,
    ShippingRateSchema,
    ShippingRateUpdateRequest,
    ShippingZoneCreateRequest,
    ShippingZoneSchema,
    ShippingZoneUpdateRequest,
)
from app.modules.logistique.application.cas_utilisation import (
    CalculateShippingUseCase,
    CreateRateUseCase,
    CreateZoneUseCase,
    DeleteRateUseCase,
    DeleteZoneUseCase,
    ListActiveZonesUseCase,
    ListRatesUseCase,
    UpdateRateUseCase,
    UpdateZoneUseCase,
)
from app.modules.logistique.domain.exceptions import (
    NoApplicableShippingRateError,
    ShippingRateNotFoundError,
    ShippingZoneNotFoundError,
)
from app.modules.logistique.infrastructure.depots import (
    SQLAlchemyShippingRateRepository,
    SQLAlchemyShippingZoneRepository,
)

router = APIRouter(tags=["Logistique"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _zone_repo(db: DbDep) -> SQLAlchemyShippingZoneRepository:
    return SQLAlchemyShippingZoneRepository(db)

def _rate_repo(db: DbDep) -> SQLAlchemyShippingRateRepository:
    return SQLAlchemyShippingRateRepository(db)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

@router.get("/livraison/zones", response_model=list[ShippingZoneSchema])
async def list_shipping_zones(
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> list[ShippingZoneSchema]:
    uc = ListActiveZonesUseCase(repo)
    zones = await uc.execute()
    return [ShippingZoneSchema.model_validate(z) for z in zones]


@router.get("/livraison/tarifs", response_model=list[ShippingRateSchema])
async def list_shipping_rates(
    id_zone: Annotated[int, Query()],
    montant: Annotated[float | None, Query(ge=0)] = None,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> list[ShippingRateSchema]:
    uc = ListRatesUseCase(repo)
    rates = await uc.execute(
        id_zone=id_zone,
        montant=Decimal(str(montant)) if montant is not None else None,
    )
    return [ShippingRateSchema.model_validate(r) for r in rates]


@router.get("/livraison/calculer", response_model=ShippingCalculationSchema)
async def calculate_shipping(
    id_zone: Annotated[int, Query()],
    montant: Annotated[float, Query(ge=0)],
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> ShippingCalculationSchema:
    uc = CalculateShippingUseCase(repo)
    try:
        result = await uc.execute(id_zone=id_zone, montant=Decimal(str(montant)))
    except NoApplicableShippingRateError as exc:
        raise HTTPException(
            status_code=statut.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ShippingCalculationSchema(
        tarif=result.tarif,
        jours_livraison_min=result.jours_livraison_min,
        jours_livraison_max=result.jours_livraison_max,
        rate_name=result.rate_name,
        livraison_gratuite=result.livraison_gratuite,
    )


# ---------------------------------------------------------------------------
# Admin — Zones
# ---------------------------------------------------------------------------

@router.post(
    "/admin/livraison/zones",
    response_model=ShippingZoneSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_zone(
    payload: ShippingZoneCreateRequest,
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> ShippingZoneSchema:
    uc = CreateZoneUseCase(repo)
    zone = await uc.execute(**payload.model_dump())
    return ShippingZoneSchema.model_validate(zone)


@router.put(
    "/admin/livraison/zones/{id_zone}",
    response_model=ShippingZoneSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_zone(
    id_zone: int,
    payload: ShippingZoneUpdateRequest,
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> ShippingZoneSchema:
    uc = UpdateZoneUseCase(repo)
    try:
        zone = await uc.execute(id_zone=id_zone, **payload.model_dump())
    except ShippingZoneNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ShippingZoneSchema.model_validate(zone)


@router.delete(
    "/admin/livraison/zones/{id_zone}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_zone(
    id_zone: int,
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> None:
    uc = DeleteZoneUseCase(repo)
    try:
        await uc.execute(id_zone)
    except ShippingZoneNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Admin — Rates
# ---------------------------------------------------------------------------

@router.post(
    "/admin/livraison/tarifs",
    response_model=ShippingRateSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_rate(
    payload: ShippingRateCreateRequest,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> ShippingRateSchema:
    uc = CreateRateUseCase(repo)
    tarif = await uc.execute(**payload.model_dump())
    return ShippingRateSchema.model_validate(tarif)


@router.put(
    "/admin/livraison/tarifs/{rate_id}",
    response_model=ShippingRateSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_rate(
    rate_id: int,
    payload: ShippingRateUpdateRequest,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> ShippingRateSchema:
    uc = UpdateRateUseCase(repo)
    try:
        tarif = await uc.execute(rate_id=rate_id, **payload.model_dump())
    except ShippingRateNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ShippingRateSchema.model_validate(tarif)


@router.delete(
    "/admin/livraison/tarifs/{rate_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_rate(
    rate_id: int,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> None:
    uc = DeleteRateUseCase(repo)
    try:
        await uc.execute(rate_id)
    except ShippingRateNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
