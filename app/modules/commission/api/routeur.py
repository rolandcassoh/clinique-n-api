"""Routeur FastAPI du module commissions."""
from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.commission.api.schemas import (
    CommissionEarningSchema,
    DoctorEarningsSummarySchema,
    EmployeeEarningSchema,
    GenerateEarningsReportRequest,
)
from app.modules.commission.application.cas_utilisation import (
    AdminListCommissionsUseCase,
    AdminListEarningsUseCase,
    AdminMarkCommissionPaidUseCase,
    GenerateEarningsReportUseCase,
    GetDoctorEarningsSummaryUseCase,
    GetDoctorEarningsUseCase,
)
from app.modules.commission.domain.exceptions import CommissionNotFoundError
from app.modules.commission.infrastructure.depots import (
    SQLAlchemyCommissionEarningRepository,
    SQLAlchemyCommissionRateRepository,
    SQLAlchemyEmployeeEarningRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Commissions"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
DoctorDep = Annotated[dict[str, Any], Depends(require_role("doctor", "admin", "super-admin"))]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _earning_repo(db: DbDep) -> SQLAlchemyCommissionEarningRepository:
    return SQLAlchemyCommissionEarningRepository(db)


def _emp_earning_repo(db: DbDep) -> SQLAlchemyEmployeeEarningRepository:
    return SQLAlchemyEmployeeEarningRepository(db)


def _rate_repo(db: DbDep) -> SQLAlchemyCommissionRateRepository:
    return SQLAlchemyCommissionRateRepository(db)


# ---------------------------------------------------------------------------
# Médecin — ses revenus
# ---------------------------------------------------------------------------

@router.get("/medecin/revenus", response_model=Page[CommissionEarningSchema])
async def get_doctor_earnings(
    current_user: DoctorDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    earning_repo: SQLAlchemyCommissionEarningRepository = Depends(_earning_repo),
) -> Page[CommissionEarningSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = GetDoctorEarningsUseCase(earning_repo)
    return await uc.execute(current_user["id"], params)  # type: ignore[return-valeur]


@router.get("/medecin/revenus/resume", response_model=DoctorEarningsSummarySchema)
async def get_doctor_earnings_summary(
    current_user: DoctorDep,
    earning_repo: SQLAlchemyCommissionEarningRepository = Depends(_earning_repo),
) -> DoctorEarningsSummarySchema:
    uc = GetDoctorEarningsSummaryUseCase(earning_repo)
    summary = await uc.execute(current_user["id"])
    return DoctorEarningsSummarySchema(**summary)


# ---------------------------------------------------------------------------
# Admin — commissions
# ---------------------------------------------------------------------------

@router.get("/admin/commissions", response_model=Page[CommissionEarningSchema])
async def admin_list_commissions(
    current_user: AdminDep,
    id_clinique: Annotated[Optional[int], Query()] = None,
    id_medecin: Annotated[Optional[int], Query()] = None,
    filter_status: Annotated[Optional[str], Query(alias="statut")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    earning_repo: SQLAlchemyCommissionEarningRepository = Depends(_earning_repo),
) -> Page[CommissionEarningSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListCommissionsUseCase(earning_repo)
    return await uc.execute(params, id_clinique, id_medecin, filter_status)  # type: ignore[return-valeur]


@router.post(
    "/admin/commissions/{commission_id}/marquer-paye",
    response_model=CommissionEarningSchema,
)
async def admin_mark_commission_paid(
    commission_id: int,
    current_user: AdminDep,
    earning_repo: SQLAlchemyCommissionEarningRepository = Depends(_earning_repo),
) -> CommissionEarningSchema:
    uc = AdminMarkCommissionPaidUseCase(earning_repo)
    try:
        earning = await uc.execute(commission_id)
    except CommissionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return CommissionEarningSchema.model_validate(earning)


# ---------------------------------------------------------------------------
# Admin — rapports revenus
# ---------------------------------------------------------------------------

@router.get("/admin/revenus", response_model=Page[EmployeeEarningSchema])
async def admin_list_earnings(
    current_user: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    emp_earning_repo: SQLAlchemyEmployeeEarningRepository = Depends(_emp_earning_repo),
) -> Page[EmployeeEarningSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListEarningsUseCase(emp_earning_repo)
    return await uc.execute(params)  # type: ignore[return-valeur]


@router.post(
    "/admin/revenus/generer",
    response_model=list[EmployeeEarningSchema],
    status_code=statut.HTTP_201_CREATED,
)
async def admin_generate_earnings_report(
    payload: GenerateEarningsReportRequest,
    current_user: AdminDep,
    earning_repo: SQLAlchemyCommissionEarningRepository = Depends(_earning_repo),
    emp_earning_repo: SQLAlchemyEmployeeEarningRepository = Depends(_emp_earning_repo),
) -> list[EmployeeEarningSchema]:
    uc = GenerateEarningsReportUseCase(emp_earning_repo, earning_repo)
    results = await uc.execute(
        debut_periode=payload.debut_periode,
        fin_periode=payload.fin_periode,
        id_clinique=payload.id_clinique,
        id_medecin=payload.id_medecin,
    )
    return [EmployeeEarningSchema.model_validate(r) for r in results]
