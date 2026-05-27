"""API router — module vital."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.vital.api.schemas import (
    VitalSignsCreateSchema,
    VitalSignsSchema,
    VitalSignsUpdateSchema,
    VitalStatsSchema,
)
from app.modules.vital.application.use_cases import (
    CreateVitalUseCase,
    DeleteVitalUseCase,
    GetVitalStatsUseCase,
    GetVitalUseCase,
    ListAdminVitalsUseCase,
    ListMyVitalsUseCase,
    UpdateVitalUseCase,
)
from app.modules.vital.domain.exceptions import (
    VitalSignsAccessDeniedError,
    VitalSignsNotFoundError,
)
from app.modules.vital.infrastructure.repositories import SQLVitalSignsRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Vitals"])

_admin_or_doctor = require_role("admin", "doctor", "receptionist")
_admin_dep = require_role("admin", "doctor")


def _vital_repo(db: AsyncSession = Depends(get_db)) -> SQLVitalSignsRepository:
    return SQLVitalSignsRepository(db)


def _vital_schema(v) -> VitalSignsSchema:
    data = v.__dict__.copy()
    data["bmi"] = v.bmi
    return VitalSignsSchema.model_validate(data)


# ── Patient — ses propres constantes ─────────────────────────────────────────

@router.get("/vitals/stats", response_model=VitalStatsSchema)
async def get_my_vital_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalStatsSchema:
    stats = await GetVitalStatsUseCase(repo).execute(current_user["id"])
    return VitalStatsSchema.model_validate(stats.__dict__)


@router.get("/vitals", response_model=Page[VitalSignsSchema])
async def list_my_vitals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> Page[VitalSignsSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListMyVitalsUseCase(repo).execute(current_user["id"], params)
    return Page[VitalSignsSchema](
        data=[_vital_schema(v) for v in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get("/vitals/{vital_id}", response_model=VitalSignsSchema)
async def get_vital(
    vital_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalSignsSchema:
    try:
        vital = await GetVitalUseCase(repo).execute(
            vital_id, current_user["id"], current_user.get("roles", [])
        )
    except VitalSignsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _vital_schema(vital)


@router.post(
    "/vitals",
    response_model=VitalSignsSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_vital(
    body: VitalSignsCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalSignsSchema:
    vital = await CreateVitalUseCase(repo).execute(
        patient_id=body.patient_id,
        recorded_by=current_user["id"],
        appointment_id=body.appointment_id,
        blood_pressure_systolic=body.blood_pressure_systolic,
        blood_pressure_diastolic=body.blood_pressure_diastolic,
        heart_rate=body.heart_rate,
        temperature=body.temperature,
        weight=body.weight,
        height=body.height,
        oxygen_saturation=body.oxygen_saturation,
        blood_sugar=body.blood_sugar,
        notes=body.notes,
        recorded_at=body.recorded_at,
    )
    return _vital_schema(vital)


@router.put("/vitals/{vital_id}", response_model=VitalSignsSchema)
async def update_vital(
    vital_id: int,
    body: VitalSignsUpdateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalSignsSchema:
    try:
        vital = await UpdateVitalUseCase(repo).execute(
            vital_id, current_user["id"], current_user.get("roles", []),
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except VitalSignsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return _vital_schema(vital)


@router.delete(
    "/vitals/{vital_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_vital(
    vital_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> None:
    try:
        await DeleteVitalUseCase(repo).execute(
            vital_id, current_user["id"], current_user.get("roles", [])
        )
    except VitalSignsNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)


# ── Admin / Doctor ────────────────────────────────────────────────────────────

@router.get(
    "/admin/vitals",
    response_model=Page[VitalSignsSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_vitals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    patient_id: Optional[int] = Query(None),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> Page[VitalSignsSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListAdminVitalsUseCase(repo).execute(params, patient_id=patient_id)
    return Page[VitalSignsSchema](
        data=[_vital_schema(v) for v in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )
