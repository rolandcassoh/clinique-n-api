"""Router FastAPI du module Logistic."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.logistic.api.schemas import (
    ShippingCalculationSchema,
    ShippingRateCreateRequest,
    ShippingRateSchema,
    ShippingRateUpdateRequest,
    ShippingZoneCreateRequest,
    ShippingZoneSchema,
    ShippingZoneUpdateRequest,
)
from app.modules.logistic.application.use_cases import (
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
from app.modules.logistic.domain.exceptions import (
    NoApplicableShippingRateError,
    ShippingRateNotFoundError,
    ShippingZoneNotFoundError,
)
from app.modules.logistic.infrastructure.repositories import (
    SQLAlchemyShippingRateRepository,
    SQLAlchemyShippingZoneRepository,
)

router = APIRouter(tags=["Logistic"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


def _zone_repo(db: DbDep) -> SQLAlchemyShippingZoneRepository:
    return SQLAlchemyShippingZoneRepository(db)

def _rate_repo(db: DbDep) -> SQLAlchemyShippingRateRepository:
    return SQLAlchemyShippingRateRepository(db)


# ---------------------------------------------------------------------------
# Public
# ---------------------------------------------------------------------------

@router.get("/shipping/zones", response_model=list[ShippingZoneSchema])
async def list_shipping_zones(
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> list[ShippingZoneSchema]:
    uc = ListActiveZonesUseCase(repo)
    zones = await uc.execute()
    return [ShippingZoneSchema.model_validate(z) for z in zones]


@router.get("/shipping/rates", response_model=list[ShippingRateSchema])
async def list_shipping_rates(
    zone_id: Annotated[int, Query()],
    amount: Annotated[float | None, Query(ge=0)] = None,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> list[ShippingRateSchema]:
    uc = ListRatesUseCase(repo)
    rates = await uc.execute(
        zone_id=zone_id,
        amount=Decimal(str(amount)) if amount is not None else None,
    )
    return [ShippingRateSchema.model_validate(r) for r in rates]


@router.get("/shipping/calculate", response_model=ShippingCalculationSchema)
async def calculate_shipping(
    zone_id: Annotated[int, Query()],
    amount: Annotated[float, Query(ge=0)],
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> ShippingCalculationSchema:
    uc = CalculateShippingUseCase(repo)
    try:
        result = await uc.execute(zone_id=zone_id, amount=Decimal(str(amount)))
    except NoApplicableShippingRateError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return ShippingCalculationSchema(
        rate=result.rate,
        estimated_days_min=result.estimated_days_min,
        estimated_days_max=result.estimated_days_max,
        rate_name=result.rate_name,
        is_free_shipping=result.is_free_shipping,
    )


# ---------------------------------------------------------------------------
# Admin — Zones
# ---------------------------------------------------------------------------

@router.post(
    "/admin/shipping/zones",
    response_model=ShippingZoneSchema,
    status_code=status.HTTP_201_CREATED,
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
    "/admin/shipping/zones/{zone_id}",
    response_model=ShippingZoneSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_zone(
    zone_id: int,
    payload: ShippingZoneUpdateRequest,
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> ShippingZoneSchema:
    uc = UpdateZoneUseCase(repo)
    try:
        zone = await uc.execute(zone_id=zone_id, **payload.model_dump())
    except ShippingZoneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ShippingZoneSchema.model_validate(zone)


@router.delete(
    "/admin/shipping/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_zone(
    zone_id: int,
    repo: SQLAlchemyShippingZoneRepository = Depends(_zone_repo),
) -> None:
    uc = DeleteZoneUseCase(repo)
    try:
        await uc.execute(zone_id)
    except ShippingZoneNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Admin — Rates
# ---------------------------------------------------------------------------

@router.post(
    "/admin/shipping/rates",
    response_model=ShippingRateSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_rate(
    payload: ShippingRateCreateRequest,
    repo: SQLAlchemyShippingRateRepository = Depends(_rate_repo),
) -> ShippingRateSchema:
    uc = CreateRateUseCase(repo)
    rate = await uc.execute(**payload.model_dump())
    return ShippingRateSchema.model_validate(rate)


@router.put(
    "/admin/shipping/rates/{rate_id}",
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
        rate = await uc.execute(rate_id=rate_id, **payload.model_dump())
    except ShippingRateNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ShippingRateSchema.model_validate(rate)


@router.delete(
    "/admin/shipping/rates/{rate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
