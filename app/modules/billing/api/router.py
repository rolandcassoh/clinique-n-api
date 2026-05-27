"""Router FastAPI du module billing."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.billing.api.schemas import (
    BillingRecordSchema,
    BillingStatsSchema,
    CreateInvoiceRequest,
    GetOrCreateInvoiceRequest,
    UpdateBillingStatusRequest,
)
from app.modules.billing.application.use_cases import (
    AdminBillingStatsUseCase,
    AdminListBillingUseCase,
    AdminUpdateBillingStatusUseCase,
    CreateInvoiceUseCase,
    GenerateInvoicePDFUseCase,
    GetBillingUseCase,
    GetOrCreateInvoiceUseCase,
    ListMyInvoicesUseCase,
)
from app.modules.billing.domain.exceptions import (
    BillingNotFoundError,
    InvoiceAlreadyExistsError,
    InvalidStatusTransitionError,
)
from app.modules.billing.infrastructure.repositories import SQLAlchemyBillingRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Billing"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]
DoctorAdminDep = Annotated[dict[str, Any], Depends(require_role("doctor", "admin", "super-admin"))]


def _billing_repo(db: DbDep) -> SQLAlchemyBillingRepository:
    return SQLAlchemyBillingRepository(db)


# ---------------------------------------------------------------------------
# RDV → Facture
# ---------------------------------------------------------------------------

@router.get("/appointments/{appointment_id}/billing", response_model=BillingRecordSchema)
async def get_appointment_billing(
    appointment_id: int,
    patient_id: Annotated[int, Query(description="ID du patient")],
    consultation_fee: Annotated[Decimal, Query(description="Honoraires en XAF", gt=0)] = Decimal("15000"),
    current_user: CurrentUserDep = None,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = GetOrCreateInvoiceUseCase(billing_repo)
    record = await uc.execute(
        appointment_id=appointment_id,
        patient_id=patient_id,
        consultation_fee=consultation_fee,
    )
    return BillingRecordSchema.model_validate(record)


@router.post(
    "/appointments/{appointment_id}/billing",
    response_model=BillingRecordSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment_billing(
    appointment_id: int,
    payload: CreateInvoiceRequest,
    current_user: DoctorAdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = CreateInvoiceUseCase(billing_repo)
    # Récupérer patient_id depuis le RDV — simplifié ici avec une valeur passée
    # En production, on ferait un join avec la table appointments
    items = [item.model_dump() for item in payload.items]
    try:
        record = await uc.execute(
            appointment_id=appointment_id,
            patient_id=current_user["id"],  # simplifié
            items=items,
            discount_amount=payload.discount_amount,
            notes=payload.notes,
        )
    except InvoiceAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


# ---------------------------------------------------------------------------
# Facture directe
# ---------------------------------------------------------------------------

@router.get("/billing/{billing_id}", response_model=BillingRecordSchema)
async def get_billing(
    billing_id: int,
    current_user: CurrentUserDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = GetBillingUseCase(billing_repo)
    try:
        record = await uc.execute(billing_id)
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


@router.get("/billing/{billing_id}/pdf")
async def get_billing_pdf(
    billing_id: int,
    current_user: CurrentUserDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Response:
    uc = GenerateInvoicePDFUseCase(billing_repo)
    try:
        pdf_bytes = await uc.execute(billing_id, patient_name="Patient")
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Détecter si WeasyPrint a généré du vrai PDF (signature %PDF) ou HTML fallback
    if pdf_bytes[:4] == b"%PDF":
        content_type = "application/pdf"
        filename = f"facture-{billing_id}.pdf"
    else:
        content_type = "text/html; charset=utf-8"
        filename = f"facture-{billing_id}.html"

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Patient — mes factures
# ---------------------------------------------------------------------------

@router.get("/my-invoices", response_model=Page[BillingRecordSchema])
async def my_invoices(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Page[BillingRecordSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyInvoicesUseCase(billing_repo)
    return await uc.execute(current_user["id"], params)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/billing", response_model=Page[BillingRecordSchema])
async def admin_list_billing(
    current_user: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Page[BillingRecordSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListBillingUseCase(billing_repo)
    return await uc.execute(params)  # type: ignore[return-value]


@router.patch("/admin/billing/{billing_id}/status", response_model=BillingRecordSchema)
async def admin_update_billing_status(
    billing_id: int,
    payload: UpdateBillingStatusRequest,
    current_user: AdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = AdminUpdateBillingStatusUseCase(billing_repo)
    try:
        record = await uc.execute(billing_id, payload.status)
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


@router.get("/admin/billing/stats", response_model=BillingStatsSchema)
async def admin_billing_stats(
    current_user: AdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingStatsSchema:
    uc = AdminBillingStatsUseCase(billing_repo)
    stats = await uc.execute()
    return BillingStatsSchema(**stats)
