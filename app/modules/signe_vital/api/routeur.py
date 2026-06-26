"""Routeur API — module constantes vitales."""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.signe_vital.api.schemas import (
    VitalSignsCreateSchema,
    VitalSignsSchema,
    VitalSignsUpdateSchema,
    VitalStatsSchema,
)
from app.modules.signe_vital.application.cas_utilisation import (
    CreateVitalUseCase,
    DeleteVitalUseCase,
    GetVitalStatsUseCase,
    GetVitalUseCase,
    ListAdminVitalsUseCase,
    ListMyVitalsUseCase,
    UpdateVitalUseCase,
)
from app.modules.signe_vital.domain.exceptions import (
    VitalSignsAccessDeniedError,
    VitalSignsNotFoundError,
)
from app.modules.signe_vital.infrastructure.depots import SQLVitalSignsRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Signes Vitaux"])

_admin_or_doctor = require_role("admin", "doctor", "receptionist")
_admin_dep = require_role("admin", "doctor")


def _vital_repo(db: AsyncSession = Depends(get_db)) -> SQLVitalSignsRepository:
    return SQLVitalSignsRepository(db)


def _vital_schema(v) -> VitalSignsSchema:
    data = v.__dict__.copy()
    data["bmi"] = v.bmi
    return VitalSignsSchema.model_validate(data)


# ── Patient — consultation de ses propres constantes ─────────────────────────

@router.get("/signes-vitaux/statistiques", response_model=VitalStatsSchema)
async def get_my_vital_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalStatsSchema:
    stats = await GetVitalStatsUseCase(repo).execute(current_user["id"])
    return VitalStatsSchema.model_validate(stats.__dict__)


@router.get("/signes-vitaux", response_model=Page[VitalSignsSchema])
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


@router.get("/signes-vitaux/{vital_id}", response_model=VitalSignsSchema)
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=exc.message)
    return _vital_schema(vital)


@router.post(
    "/signes-vitaux",
    response_model=VitalSignsSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_vital(
    body: VitalSignsCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> VitalSignsSchema:
    vital = await CreateVitalUseCase(repo).execute(
        id_patient=body.id_patient,
        enregistre_par=current_user["id"],
        id_rendez_vous=body.id_rendez_vous,
        tension_systolique=body.tension_systolique,
        tension_diastolique=body.tension_diastolique,
        frequence_cardiaque=body.frequence_cardiaque,
        temperature=body.temperature,
        poids=body.poids,
        taille=body.taille,
        saturation_oxygene=body.saturation_oxygene,
        glycemie=body.glycemie,
        notes=body.notes,
        enregistre_le=body.enregistre_le,
    )
    return _vital_schema(vital)


@router.put("/signes-vitaux/{vital_id}", response_model=VitalSignsSchema)
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=exc.message)
    return _vital_schema(vital)


@router.delete(
    "/signes-vitaux/{vital_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except VitalSignsAccessDeniedError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=exc.message)


# ── Admin / Médecin — gestion globale des constantes ─────────────────────────

@router.get(
    "/admin/signes-vitaux",
    response_model=Page[VitalSignsSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_vitals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    id_patient: Optional[int] = Query(None),
    repo: SQLVitalSignsRepository = Depends(_vital_repo),
) -> Page[VitalSignsSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListAdminVitalsUseCase(repo).execute(params, id_patient=id_patient)
    return Page[VitalSignsSchema](
        data=[_vital_schema(v) for v in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )
