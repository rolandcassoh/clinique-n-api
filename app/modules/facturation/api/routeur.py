"""Routeur FastAPI du module facturation."""
from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.facturation.api.schemas import (
    BillingRecordSchema,
    BillingStatsSchema,
    CreateInvoiceRequest,
    GetOrCreateInvoiceRequest,
    UpdateBillingStatusRequest,
)
from app.modules.facturation.application.cas_utilisation import (
    AdminBillingStatsUseCase,
    AdminListBillingUseCase,
    AdminUpdateBillingStatusUseCase,
    CreateInvoiceUseCase,
    GenerateInvoicePDFUseCase,
    GetBillingUseCase,
    GetOrCreateInvoiceUseCase,
    ListMyInvoicesUseCase,
)
from app.modules.facturation.domain.exceptions import (
    BillingNotFoundError,
    InvoiceAlreadyExistsError,
    InvalidStatusTransitionError,
)
from app.modules.facturation.infrastructure.depots import SQLAlchemyBillingRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Facturation"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]
DoctorAdminDep = Annotated[dict[str, Any], Depends(require_role("doctor", "admin", "super-admin"))]


def _billing_repo(db: DbDep) -> SQLAlchemyBillingRepository:
    return SQLAlchemyBillingRepository(db)


# ---------------------------------------------------------------------------
# RDV → Facture
# ---------------------------------------------------------------------------

@router.get("/rendez-vous/{id_rendez_vous}/facturation", response_model=BillingRecordSchema)
async def get_appointment_billing(
    id_rendez_vous: int,
    id_patient: Annotated[int, Query(description="ID du patient")],
    honoraires_consultation: Annotated[Decimal, Query(description="Honoraires en XAF", gt=0)] = Decimal("15000"),
    current_user: CurrentUserDep = None,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = GetOrCreateInvoiceUseCase(billing_repo)
    record = await uc.execute(
        id_rendez_vous=id_rendez_vous,
        id_patient=id_patient,
        honoraires_consultation=honoraires_consultation,
    )
    return BillingRecordSchema.model_validate(record)


@router.post(
    "/rendez-vous/{id_rendez_vous}/facturation",
    response_model=BillingRecordSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_appointment_billing(
    id_rendez_vous: int,
    payload: CreateInvoiceRequest,
    current_user: DoctorAdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = CreateInvoiceUseCase(billing_repo)
    # Récupération du id_patient depuis le RDV — simplifié ici avec la valeur fournie
    # En production, une jointure avec la table appointments serait effectuée
    elements = [item.model_dump() for item in payload.items]
    try:
        record = await uc.execute(
            id_rendez_vous=id_rendez_vous,
            id_patient=current_user["id"],  # simplifié
            items=elements,
            montant_remise=payload.montant_remise,
            notes=payload.notes,
        )
    except InvoiceAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


# ---------------------------------------------------------------------------
# Facture directe
# ---------------------------------------------------------------------------

@router.get("/factures/{id_facture}", response_model=BillingRecordSchema)
async def get_billing(
    id_facture: int,
    current_user: CurrentUserDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = GetBillingUseCase(billing_repo)
    try:
        record = await uc.execute(id_facture)
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


@router.get("/factures/{id_facture}/telecharger")
async def get_billing_pdf(
    id_facture: int,
    current_user: CurrentUserDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Response:
    uc = GenerateInvoicePDFUseCase(billing_repo)
    try:
        pdf_bytes = await uc.execute(id_facture, patient_name="Patient")
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    # Détecter si WeasyPrint a généré un vrai PDF (signature %PDF) ou un repli HTML
    if pdf_bytes[:4] == b"%PDF":
        content_type = "application/pdf"
        filename = f"facture-{id_facture}.pdf"
    else:
        content_type = "text/html; charset=utf-8"
        filename = f"facture-{id_facture}.html"

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Patient — mes factures
# ---------------------------------------------------------------------------

@router.get("/mes-factures", response_model=Page[BillingRecordSchema])
async def my_invoices(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Page[BillingRecordSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyInvoicesUseCase(billing_repo)
    return await uc.execute(current_user["id"], params)  # type: ignore[return-valeur]


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/facturation", response_model=Page[BillingRecordSchema])
async def admin_list_billing(
    current_user: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> Page[BillingRecordSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListBillingUseCase(billing_repo)
    return await uc.execute(params)  # type: ignore[return-valeur]


@router.patch("/admin/facturation/{id_facture}/statut", response_model=BillingRecordSchema)
async def admin_update_billing_status(
    id_facture: int,
    payload: UpdateBillingStatusRequest,
    current_user: AdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingRecordSchema:
    uc = AdminUpdateBillingStatusUseCase(billing_repo)
    try:
        record = await uc.execute(id_facture, payload.statut)
    except BillingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return BillingRecordSchema.model_validate(record)


@router.get("/admin/facturation/statistiques", response_model=BillingStatsSchema)
async def admin_billing_stats(
    current_user: AdminDep,
    billing_repo: SQLAlchemyBillingRepository = Depends(_billing_repo),
) -> BillingStatsSchema:
    uc = AdminBillingStatsUseCase(billing_repo)
    stats = await uc.execute()
    return BillingStatsSchema(**stats)
