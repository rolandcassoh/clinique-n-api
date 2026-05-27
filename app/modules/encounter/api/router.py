"""Router FastAPI du module encounter."""
from __future__ import annotations

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.encounter.api.schemas import (
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
from app.modules.encounter.application.use_cases import (
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
from app.modules.encounter.domain.exceptions import (
    BodyChartNotFoundError,
    EncounterNotFoundError,
    MedicalReportNotFoundError,
    PrescriptionNotFoundError,
    UnauthorizedMedicalAccessError,
)
from app.modules.encounter.infrastructure.repositories import (
    SQLAlchemyBodyChartRepository,
    SQLAlchemyEncounterRepository,
    SQLAlchemyMedicalReportRepository,
    SQLAlchemyPrescriptionRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Encounters"])

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


# ---------------------------------------------------------------------------
# Médecin — Consultations
# ---------------------------------------------------------------------------

@router.post(
    "/encounters",
    response_model=EncounterSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_encounter(
    payload: EncounterCreateRequest,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = CreateEncounterUseCase(enc_repo)
    enc = await uc.execute(
        doctor_id=current_user["id"],
        patient_id=payload.patient_id,
        appointment_id=payload.appointment_id,
        chief_complaint=payload.chief_complaint,
    )
    return EncounterSchema.model_validate(enc)


@router.get("/encounters/{encounter_id}", response_model=EncounterSchema)
async def get_encounter(
    encounter_id: int,
    current_user: CurrentUserDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = GetEncounterUseCase(enc_repo)
    try:
        enc = await uc.execute(encounter_id)
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EncounterSchema.model_validate(enc)


@router.put("/encounters/{encounter_id}", response_model=EncounterSchema)
async def update_encounter(
    encounter_id: int,
    payload: EncounterUpdateRequest,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> EncounterSchema:
    uc = UpdateEncounterUseCase(enc_repo)
    try:
        enc = await uc.execute(
            encounter_id=encounter_id,
            follow_up_date=payload.follow_up_date,
            follow_up_notes=payload.follow_up_notes,
            status=payload.status,
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EncounterSchema.model_validate(enc)


# ---------------------------------------------------------------------------
# Rapport médical
# ---------------------------------------------------------------------------

@router.get("/encounters/{encounter_id}/medical-report", response_model=MedicalReportSchema)
async def get_medical_report(
    encounter_id: int,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    report_repo: SQLAlchemyMedicalReportRepository = Depends(_report_repo),
) -> MedicalReportSchema:
    uc = GetMedicalReportUseCase(report_repo, enc_repo)
    try:
        report = await uc.execute(encounter_id, current_user["id"])
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except MedicalReportNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MedicalReportSchema.model_validate(report)


@router.post(
    "/encounters/{encounter_id}/medical-report",
    response_model=MedicalReportSchema,
    status_code=status.HTTP_201_CREATED,
)
async def upsert_medical_report(
    encounter_id: int,
    payload: MedicalReportCreateRequest,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    report_repo: SQLAlchemyMedicalReportRepository = Depends(_report_repo),
) -> MedicalReportSchema:
    uc = UpsertMedicalReportUseCase(report_repo, enc_repo)
    try:
        report = await uc.execute(
            encounter_id=encounter_id,
            requesting_doctor_id=current_user["id"],
            **payload.model_dump(exclude_none=True),
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return MedicalReportSchema.model_validate(report)


# ---------------------------------------------------------------------------
# Ordonnances
# ---------------------------------------------------------------------------

@router.get(
    "/encounters/{encounter_id}/prescriptions",
    response_model=list[PrescriptionSchema],
)
async def list_prescriptions(
    encounter_id: int,
    current_user: DoctorDep,
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> list[PrescriptionSchema]:
    uc = ListPrescriptionsUseCase(presc_repo)
    prescriptions = await uc.execute(encounter_id)
    return [PrescriptionSchema.model_validate(p) for p in prescriptions]


@router.post(
    "/encounters/{encounter_id}/prescriptions",
    response_model=PrescriptionSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_prescription(
    encounter_id: int,
    payload: PrescriptionCreateRequest,
    current_user: DoctorDep,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> PrescriptionSchema:
    uc = CreatePrescriptionUseCase(presc_repo, enc_repo)
    try:
        presc = await uc.execute(
            encounter_id=encounter_id,
            requesting_doctor_id=current_user["id"],
            medication_name=payload.medication_name,
            dosage=payload.dosage,
            frequency=payload.frequency,
            duration_days=payload.duration_days,
            instructions=payload.instructions,
            is_chronic=payload.is_chronic,
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except UnauthorizedMedicalAccessError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return PrescriptionSchema.model_validate(presc)


@router.delete(
    "/encounters/{encounter_id}/prescriptions/{prescription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_prescription(
    encounter_id: int,
    prescription_id: int,
    current_user: DoctorDep,
    presc_repo: SQLAlchemyPrescriptionRepository = Depends(_presc_repo),
) -> None:
    uc = DeletePrescriptionUseCase(presc_repo)
    try:
        await uc.execute(prescription_id)
    except PrescriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Patient — accès limité
# ---------------------------------------------------------------------------

@router.get("/my-encounters", response_model=Page[EncounterSchema])
async def my_encounters(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> Page[EncounterSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListMyEncountersUseCase(enc_repo)
    result = await uc.execute(current_user["id"], params)
    return result  # type: ignore[return-value]


@router.get("/my-prescriptions", response_model=list[PrescriptionSchema])
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
    "/appointments/{appointment_id}/bodychart",
    response_model=BodyChartSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_bodychart(
    appointment_id: int,
    payload: BodyChartCreateRequest,
    current_user: DoctorDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = UpsertBodyChartUseCase(chart_repo)
    chart = await uc.execute(
        appointment_id=appointment_id,
        image_url=payload.image_url,
        annotations=payload.annotations,
        notes=payload.notes,
    )
    return BodyChartSchema.model_validate(chart)


@router.get("/appointments/{appointment_id}/bodychart", response_model=BodyChartSchema)
async def get_bodychart(
    appointment_id: int,
    current_user: CurrentUserDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = GetBodyChartUseCase(chart_repo)
    try:
        chart = await uc.execute(appointment_id)
    except BodyChartNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BodyChartSchema.model_validate(chart)


@router.put("/appointments/{appointment_id}/bodychart", response_model=BodyChartSchema)
async def update_bodychart(
    appointment_id: int,
    payload: BodyChartCreateRequest,
    current_user: DoctorDep,
    chart_repo: SQLAlchemyBodyChartRepository = Depends(_chart_repo),
) -> BodyChartSchema:
    uc = UpsertBodyChartUseCase(chart_repo)
    chart = await uc.execute(
        appointment_id=appointment_id,
        image_url=payload.image_url,
        annotations=payload.annotations,
        notes=payload.notes,
    )
    return BodyChartSchema.model_validate(chart)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/encounters", response_model=Page[EncounterSchema])
async def admin_list_encounters(
    current_user: AdminDep,
    patient_id: Annotated[Optional[int], Query()] = None,
    doctor_id: Annotated[Optional[int], Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    enc_repo: SQLAlchemyEncounterRepository = Depends(_enc_repo),
) -> Page[EncounterSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListEncountersUseCase(enc_repo)
    result = await uc.execute(params, patient_id, doctor_id)
    return result  # type: ignore[return-value]
