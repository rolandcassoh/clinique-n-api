"""Routeur FastAPI du module consultations médicales."""
from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.consultation.api.schemas import (
    BodyChartCreateRequest,
    BodyChartSchema,
    EncounterCreateRequest,
    EncounterSchema,
    EncounterUpdateRequest,
    MedicalReportCreateRequest,
    MedicalReportSchema,
    PrescriptionCreateRequest,
    PrescriptionSchema,
)
from app.modules.consultation.application.cas_utilisation import (
    AdminListEncountersUseCase,
    CreateEncounterUseCase,
    CreatePrescriptionUseCase,
    DeletePrescriptionUseCase,
    GetBodyChartUseCase,
    GetEncounterUseCase,
    GetMedicalReportUseCase,
    ListMyEncountersUseCase,
    ListMyPrescriptionsUseCase,
    ListPrescriptionsUseCase,
    UpdateEncounterUseCase,
    UpsertBodyChartUseCase,
    UpsertMedicalReportUseCase,
)
from app.modules.consultation.domain.exceptions import (
    BodyChartNotFoundError,
    EncounterNotFoundError,
    MedicalReportNotFoundError,
    PrescriptionNotFoundError,
    UnauthorizedMedicalAccessError,
)
from app.modules.consultation.infrastructure.depots import (
    SQLAlchemyBodyChartRepository,
    SQLAlchemyEncounterRepository,
    SQLAlchemyMedicalReportRepository,
    SQLAlchemyPrescriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Consultations"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
DoctorDep = Annotated[dict[str, Any], Depends(require_role("doctor", "admin", "super-admin"))]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _enc_repo(db: DbDep) -> SQLAlchemyEncounterRepository:
    return SQLAlchemyEncounterRepository(db)


def _report_repo(db: DbDep) -> SQLAlchemyMedicalReportRepository:
    return SQLAlchemyMedicalReportRepository(db)


def _presc_repo(db: DbDep) -> SQLAlchemyPrescriptionRepository:
    return SQLAlchemyPrescriptionRepository(db)


def _chart_repo(db: DbDep) -> SQLAlchemyBodyChartRepository:
    return SQLAlchemyBodyChartRepository(db)


async def _resolve_id_medecin(user: dict[str, Any], db: AsyncSession) -> int:
    """Résout medecins.id à partir de l'utilisateur connecté (utilisateurs.id != medecins.id)."""
    from sqlalchemy import select

    from app.modules.clinic.infrastructure.modeles import DoctorModel

    q = select(DoctorModel.id).where(DoctorModel.id_utilisateur == user["id"])
    id_medecin = (await db.execute(q)).scalar_one_or_none()
    return id_medecin if id_medecin is not None else user["id"]


# ---------------------------------------------------------------------------
# Médecin — Consultations
# ---------------------------------------------------------------------------

@router.post(
    "/consultations",
    response_model=EncounterSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_encounter(
    payload: EncounterCreateRequest,
    current_user: DoctorDep,
    db: DbDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = CreateEncounterUseCase(enc_repo)
    id_medecin = await _resolve_id_medecin(current_user, db)
    try:
        enc = await uc.execute(
            id_medecin=id_medecin,
            id_patient=payload.id_patient,
            id_rendez_vous=payload.id_rendez_vous,
            motif_principal=payload.motif_principal,
        )
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=statut.HTTP_409_CONFLICT,
            detail="Une consultation existe déjà pour ce rendez-vous.",
        ) from exc
    return EncounterSchema.model_validate(enc)


@router.get("/consultations/{id_consultation}", response_model=EncounterSchema)
async def get_encounter(
    id_consultation: int,
    current_user: CurrentUserDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = GetEncounterUseCase(enc_repo)
    try:
        enc = await uc.execute(id_consultation)
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EncounterSchema.model_validate(enc)


@router.put("/consultations/{id_consultation}", response_model=EncounterSchema)
async def update_encounter(
    id_consultation: int,
    payload: EncounterUpdateRequest,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = UpdateEncounterUseCase(enc_repo)
    try:
        enc = await uc.execute(
            id_consultation=id_consultation,
            date_suivi=payload.date_suivi,
            notes_suivi=payload.notes_suivi,
            statut=payload.statut,
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EncounterSchema.model_validate(enc)


# ---------------------------------------------------------------------------
# Rapport médical
# ---------------------------------------------------------------------------

@router.get("/consultations/{id_consultation}/rapport-medical", response_model=MedicalReportSchema)
async def get_medical_report(
    id_consultation: int,
    current_user: DoctorDep,
    db: DbDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    report_repo: SQLAlchemyMedicalReportRepository = Depends(_report_repo),
) -> MedicalReportSchema:
    uc = GetMedicalReportUseCase(report_repo, enc_repo)
    id_medecin = await _resolve_id_medecin(current_user, db)
    try:
        report = await uc.execute(id_consultation, id_medecin)
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except MedicalReportNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MedicalReportSchema.model_validate(report)


@router.post(
    "/consultations/{id_consultation}/rapport-medical",
    response_model=MedicalReportSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def upsert_medical_report(
    id_consultation: int,
    payload: MedicalReportCreateRequest,
    current_user: DoctorDep,
    db: DbDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    report_repo: SQLAlchemyMedicalReportRepository = Depends(_report_repo),
) -> MedicalReportSchema:
    uc = UpsertMedicalReportUseCase(report_repo, enc_repo)
    id_medecin = await _resolve_id_medecin(current_user, db)
    try:
        report = await uc.execute(
            id_consultation=id_consultation,
            requesting_doctor_id=id_medecin,
            **payload.model_dump(exclude_none=True),
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return MedicalReportSchema.model_validate(report)


# ---------------------------------------------------------------------------
# Ordonnances
# ---------------------------------------------------------------------------

@router.get(
    "/consultations/{id_consultation}/ordonnances",
    response_model=list[PrescriptionSchema],
)
async def list_prescriptions(
    id_consultation: int,
    current_user: DoctorDep,
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> list[PrescriptionSchema]:
    uc = ListPrescriptionsUseCase(presc_repo)
    prescriptions = await uc.execute(id_consultation)
    return [PrescriptionSchema.model_validate(p) for p in prescriptions]


@router.post(
    "/consultations/{id_consultation}/ordonnances",
    response_model=PrescriptionSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_prescription(
    id_consultation: int,
    payload: PrescriptionCreateRequest,
    current_user: DoctorDep,
    db: DbDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> PrescriptionSchema:
    uc = CreatePrescriptionUseCase(presc_repo, enc_repo)
    id_medecin = await _resolve_id_medecin(current_user, db)
    try:
        presc = await uc.execute(
            id_consultation=id_consultation,
            requesting_doctor_id=id_medecin,
            nom_medicament=payload.nom_medicament,
            posologie=payload.posologie,
            frequence=payload.frequence,
            duree_jours=payload.duree_jours,
            instructions=payload.instructions,
            est_chronique=payload.est_chronique,
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return PrescriptionSchema.model_validate(presc)


@router.delete(
    "/consultations/{id_consultation}/ordonnances/{prescription_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_prescription(
    id_consultation: int,
    prescription_id: int,
    current_user: DoctorDep,
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> None:
    uc = DeletePrescriptionUseCase(presc_repo)
    try:
        await uc.execute(prescription_id)
    except PrescriptionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Médecin — ses consultations
# ---------------------------------------------------------------------------

@router.get("/medecin/consultations", response_model=Page[EncounterSchema])
async def list_my_doctor_encounters(
    current_user: DoctorDep,
    db: DbDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> Page[EncounterSchema]:
    """Liste les consultations créées par le médecin connecté.

    Aucun endpoint doctor-scoped n'existait auparavant (seul /mes-consultations,
    réservé aux patients, et /admin/consultations, réservé aux admins). On réutilise
    ici AdminListEncountersUseCase filtré par medecins.id résolu.
    """
    params = PaginationParams(page=page, per_page=per_page)
    id_medecin = await _resolve_id_medecin(current_user, db)
    uc = AdminListEncountersUseCase(enc_repo)
    result = await uc.execute(params, None, id_medecin)
    return result  # type: ignore[return-valeur]


# ---------------------------------------------------------------------------
# Patient — accès limité
# ---------------------------------------------------------------------------

@router.get("/mes-consultations", response_model=Page[EncounterSchema])
async def my_encounters(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> Page[EncounterSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyEncountersUseCase(enc_repo)
    result = await uc.execute(current_user["id"], params)
    return result  # type: ignore[return-valeur]


@router.get("/mes-ordonnances", response_model=list[PrescriptionSchema])
async def my_prescriptions(
    current_user: CurrentUserDep,
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> list[PrescriptionSchema]:
    uc = ListMyPrescriptionsUseCase(presc_repo)
    prescriptions = await uc.execute(current_user["id"])
    return [PrescriptionSchema.model_validate(p) for p in prescriptions]


# ---------------------------------------------------------------------------
# Body Charts
# ---------------------------------------------------------------------------

@router.post(
    "/rendez-vous/{id_rendez_vous}/schema-corporel",
    response_model=BodyChartSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_bodychart(
    id_rendez_vous: int,
    payload: BodyChartCreateRequest,
    current_user: DoctorDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = UpsertBodyChartUseCase(chart_repo)
    chart = await uc.execute(
        id_rendez_vous=id_rendez_vous,
        url_image=payload.url_image,
        annotations=payload.annotations,
        notes=payload.notes,
    )
    return BodyChartSchema.model_validate(chart)


@router.get("/rendez-vous/{id_rendez_vous}/schema-corporel", response_model=BodyChartSchema)
async def get_bodychart(
    id_rendez_vous: int,
    current_user: CurrentUserDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = GetBodyChartUseCase(chart_repo)
    try:
        chart = await uc.execute(id_rendez_vous)
    except BodyChartNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BodyChartSchema.model_validate(chart)


@router.put("/rendez-vous/{id_rendez_vous}/schema-corporel", response_model=BodyChartSchema)
async def update_bodychart(
    id_rendez_vous: int,
    payload: BodyChartCreateRequest,
    current_user: DoctorDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = UpsertBodyChartUseCase(chart_repo)
    chart = await uc.execute(
        id_rendez_vous=id_rendez_vous,
        url_image=payload.url_image,
        annotations=payload.annotations,
        notes=payload.notes,
    )
    return BodyChartSchema.model_validate(chart)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/consultations", response_model=Page[EncounterSchema])
async def admin_list_encounters(
    current_user: AdminDep,
    id_patient: Annotated[Optional[int], Query()] = None,
    id_medecin: Annotated[Optional[int], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> Page[EncounterSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListEncountersUseCase(enc_repo)
    result = await uc.execute(params, id_patient, id_medecin)
    return result  # type: ignore[return-valeur]
