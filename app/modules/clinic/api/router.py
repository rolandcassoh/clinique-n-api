"""API router — module clinic (~86 endpoints)."""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.clinic.api.schemas import (
    AvailableSlotsSchema,
    ClinicCategoryCreateSchema,
    ClinicCategorySchema,
    ClinicCategoryUpdateSchema,
    ClinicCreateSchema,
    ClinicSchema,
    ClinicServiceCreateSchema,
    ClinicServiceSchema,
    ClinicServiceUpdateSchema,
    ClinicUpdateSchema,
    DoctorAvailabilitySchema,
    DoctorCreateSchema,
    DoctorUpdateSchema,
    DoctorLeaveCreateSchema,
    DoctorLeaveSchema,
    DoctorRatingCreateSchema,
    DoctorRatingSchema,
    DoctorSchema,
    DoctorSessionCreateSchema,
    DoctorSessionSchema,
    DoctorSessionUpdateSchema,
    ReceptionistCreateSchema,
    ReceptionistSchema,
)
from app.modules.clinic.application.use_cases import (
    ApproveRatingUseCase,
    CreateCategoryUseCase,
    CreateClinicServiceUseCase,
    CreateClinicUseCase,
    CreateDoctorLeaveUseCase,
    CreateDoctorSessionUseCase,
    CreateDoctorUseCase,
    CreateReceptionistUseCase,
    DeleteCategoryUseCase,
    DeleteClinicServiceUseCase,
    DeleteClinicUseCase,
    DeleteDoctorLeaveUseCase,
    DeleteDoctorSessionUseCase,
    DeleteDoctorUseCase,
    DeleteRatingUseCase,
    DeleteReceptionistUseCase,
    GetAvailableSlotsUseCase,
    GetClinicBySlugUseCase,
    GetDoctorScheduleUseCase,
    GetDoctorUseCase,
    ListApprovedRatingsUseCase,
    ListCategoriesUseCase,
    ListClinicServicesUseCase,
    ListClinicsUseCase,
    ListDoctorLeavesUseCase,
    ListDoctorSessionsUseCase,
    ListDoctorsUseCase,
    ListPendingRatingsUseCase,
    RateDoctorUseCase,
    ToggleClinicActiveUseCase,
    ToggleDoctorAvailabilityUseCase,
    UpdateCategoryUseCase,
    UpdateClinicServiceUseCase,
    UpdateClinicUseCase,
    UpdateDoctorSessionUseCase,
    UpdateDoctorUseCase,
)
from app.modules.clinic.domain.exceptions import (
    ClinicCategoryNotFoundError,
    ClinicNotFoundError,
    ClinicServiceNotFoundError,
    DoctorLeaveNotFoundError,
    DoctorNotFoundError,
    DoctorRatingNotFoundError,
    DoctorSessionNotFoundError,
    DuplicateRatingError,
    ReceptionistNotFoundError,
    SlugAlreadyExistsError,
)
from app.modules.clinic.infrastructure.repositories import (
    SQLClinicCategoryRepository,
    SQLClinicRepository,
    SQLClinicServiceRepository,
    SQLDoctorLeaveRepository,
    SQLDoctorRatingRepository,
    SQLDoctorRepository,
    SQLDoctorSessionRepository,
    SQLReceptionistRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Clinic"])

_admin_dep = require_role("admin", "super-admin")


# ── Dependency factories ──────────────────────────────────────────────────────

def _clinic_repo(db: AsyncSession = Depends(get_db)) -> SQLClinicRepository:
    return SQLClinicRepository(db)


def _category_repo(db: AsyncSession = Depends(get_db)) -> SQLClinicCategoryRepository:
    return SQLClinicCategoryRepository(db)


def _service_repo(db: AsyncSession = Depends(get_db)) -> SQLClinicServiceRepository:
    return SQLClinicServiceRepository(db)


def _doctor_repo(db: AsyncSession = Depends(get_db)) -> SQLDoctorRepository:
    return SQLDoctorRepository(db)


def _session_repo(db: AsyncSession = Depends(get_db)) -> SQLDoctorSessionRepository:
    return SQLDoctorSessionRepository(db)


def _leave_repo(db: AsyncSession = Depends(get_db)) -> SQLDoctorLeaveRepository:
    return SQLDoctorLeaveRepository(db)


def _rating_repo(db: AsyncSession = Depends(get_db)) -> SQLDoctorRatingRepository:
    return SQLDoctorRatingRepository(db)


def _receptionist_repo(db: AsyncSession = Depends(get_db)) -> SQLReceptionistRepository:
    return SQLReceptionistRepository(db)


# ── Public — Cliniques ────────────────────────────────────────────────────────

@router.get("/clinics", response_model=Page[ClinicSchema])
async def list_clinics(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    city_id: Optional[int] = Query(None),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_featured: Optional[bool] = Query(None),
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> Page[ClinicSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListClinicsUseCase(repo).execute(
        params, city_id=city_id, category_id=category_id,
        search=search, is_featured=is_featured,
    )
    return Page[ClinicSchema](
        data=[ClinicSchema.model_validate(c.__dict__) for c in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get("/clinics/{slug}", response_model=ClinicSchema)
async def get_clinic(
    slug: str,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await GetClinicBySlugUseCase(repo).execute(slug)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.get("/clinic-categories", response_model=list[ClinicCategorySchema])
async def list_categories(
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> list[ClinicCategorySchema]:
    categories = await ListCategoriesUseCase(repo).execute()
    return [ClinicCategorySchema.model_validate(c.__dict__) for c in categories]


# ── Public — Médecins ─────────────────────────────────────────────────────────

@router.get("/doctors", response_model=Page[DoctorSchema])
async def list_doctors(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    clinic_id: Optional[int] = Query(None),
    speciality: Optional[str] = Query(None),
    city_id: Optional[int] = Query(None),
    min_fee: Optional[Decimal] = Query(None),
    max_fee: Optional[Decimal] = Query(None),
    search: Optional[str] = Query(None),
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> Page[DoctorSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListDoctorsUseCase(repo).execute(
        params, clinic_id=clinic_id, speciality=speciality,
        city_id=city_id, min_fee=min_fee, max_fee=max_fee, search=search,
    )
    return Page[DoctorSchema](
        data=[DoctorSchema.model_validate(d.__dict__) for d in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get("/doctors/{doctor_id}", response_model=DoctorSchema)
async def get_doctor(
    doctor_id: int,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await GetDoctorUseCase(repo).execute(doctor_id)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


@router.get("/doctors/{doctor_id}/slots", response_model=AvailableSlotsSchema)
async def get_available_slots(
    doctor_id: int,
    slot_date: date = Query(..., alias="date"),
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> AvailableSlotsSchema:
    slots = await GetAvailableSlotsUseCase(repo).execute(doctor_id, slot_date)
    return AvailableSlotsSchema(doctor_id=doctor_id, date=slot_date, slots=slots)


@router.get("/doctors/{doctor_id}/schedule", response_model=list[DoctorSessionSchema])
async def get_doctor_schedule(
    doctor_id: int,
    s_repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> list[DoctorSessionSchema]:
    sessions = await GetDoctorScheduleUseCase(s_repo).execute(doctor_id)
    return [DoctorSessionSchema.model_validate(s.__dict__) for s in sessions]


@router.get("/doctors/{doctor_id}/ratings", response_model=Page[DoctorRatingSchema])
async def list_doctor_ratings(
    doctor_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> Page[DoctorRatingSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListApprovedRatingsUseCase(repo).execute(doctor_id, params)
    return Page[DoctorRatingSchema](
        data=[DoctorRatingSchema.model_validate(r.__dict__) for r in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


# ── Authentifié — Notation ────────────────────────────────────────────────────

@router.post(
    "/doctors/{doctor_id}/ratings",
    response_model=DoctorRatingSchema,
    status_code=status.HTTP_201_CREATED,
)
async def rate_doctor(
    doctor_id: int,
    body: DoctorRatingCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> DoctorRatingSchema:
    try:
        rating = await RateDoctorUseCase(repo).execute(
            doctor_id=doctor_id,
            user_id=current_user["id"],
            rating=body.rating,
            comment=body.comment,
            appointment_id=body.appointment_id,
        )
    except DuplicateRatingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return DoctorRatingSchema.model_validate(rating.__dict__)


# ── Admin — Cliniques ─────────────────────────────────────────────────────────

@router.post(
    "/admin/clinics",
    response_model=ClinicSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_clinic(
    body: ClinicCreateSchema,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await CreateClinicUseCase(repo).execute(
            owner_id=body.owner_id, name=body.name, slug=body.slug,
            description=body.description, address=body.address,
            city_id=body.city_id, phone=body.phone, email=body.email,
            website=body.website, logo=body.logo, cover_image=body.cover_image,
            latitude=body.latitude, longitude=body.longitude,
            commission_rate=body.commission_rate,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.put(
    "/admin/clinics/{clinic_id}",
    response_model=ClinicSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_clinic(
    clinic_id: int,
    body: ClinicUpdateSchema,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await UpdateClinicUseCase(repo).execute(
            clinic_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.delete(
    "/admin/clinics/{clinic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_clinic(
    clinic_id: int,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> None:
    try:
        await DeleteClinicUseCase(repo).execute(clinic_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.patch(
    "/admin/clinics/{clinic_id}/toggle",
    response_model=ClinicSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_toggle_clinic(
    clinic_id: int,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await ToggleClinicActiveUseCase(repo).execute(clinic_id)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


# ── Admin — Catégories ────────────────────────────────────────────────────────

@router.post(
    "/admin/clinic-categories",
    response_model=ClinicCategorySchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_category(
    body: ClinicCategoryCreateSchema,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> ClinicCategorySchema:
    cat = await CreateCategoryUseCase(repo).execute(
        name=body.name, slug=body.slug, image=body.image, description=body.description,
    )
    return ClinicCategorySchema.model_validate(cat.__dict__)


@router.put(
    "/admin/clinic-categories/{category_id}",
    response_model=ClinicCategorySchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_category(
    category_id: int,
    body: ClinicCategoryUpdateSchema,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> ClinicCategorySchema:
    try:
        cat = await UpdateCategoryUseCase(repo).execute(
            category_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicCategorySchema.model_validate(cat.__dict__)


@router.delete(
    "/admin/clinic-categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_category(
    category_id: int,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> None:
    try:
        await DeleteCategoryUseCase(repo).execute(category_id)
    except ClinicCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Services clinique ─────────────────────────────────────────────────

@router.get(
    "/admin/clinics/{clinic_id}/services",
    response_model=list[ClinicServiceSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_services(
    clinic_id: int,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> list[ClinicServiceSchema]:
    services = await ListClinicServicesUseCase(repo).execute(clinic_id)
    return [ClinicServiceSchema.model_validate(s.__dict__) for s in services]


@router.post(
    "/admin/clinics/{clinic_id}/services",
    response_model=ClinicServiceSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_service(
    clinic_id: int,
    body: ClinicServiceCreateSchema,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> ClinicServiceSchema:
    service = await CreateClinicServiceUseCase(repo).execute(
        clinic_id=clinic_id, name=body.name, description=body.description,
        price=body.price, duration_minutes=body.duration_minutes,
    )
    return ClinicServiceSchema.model_validate(service.__dict__)


@router.put(
    "/admin/clinics/{clinic_id}/services/{service_id}",
    response_model=ClinicServiceSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_service(
    clinic_id: int,
    service_id: int,
    body: ClinicServiceUpdateSchema,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> ClinicServiceSchema:
    try:
        service = await UpdateClinicServiceUseCase(repo).execute(
            service_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicServiceSchema.model_validate(service.__dict__)


@router.delete(
    "/admin/clinics/{clinic_id}/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_service(
    clinic_id: int,
    service_id: int,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> None:
    try:
        await DeleteClinicServiceUseCase(repo).execute(service_id)
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Médecins ──────────────────────────────────────────────────────────

@router.post(
    "/admin/clinics/{clinic_id}/doctors",
    response_model=DoctorSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_doctor(
    clinic_id: int,
    body: DoctorCreateSchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    doctor = await CreateDoctorUseCase(repo).execute(
        user_id=body.user_id, clinic_id=clinic_id,
        speciality=body.speciality, qualification=body.qualification,
        experience_years=body.experience_years,
        consultation_fee=body.consultation_fee,
        advance_payment_amount=body.advance_payment_amount,
    )
    return DoctorSchema.model_validate(doctor.__dict__)


@router.put(
    "/admin/doctors/{doctor_id}",
    response_model=DoctorSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_doctor(
    doctor_id: int,
    body: DoctorUpdateSchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await UpdateDoctorUseCase(repo).execute(
            doctor_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


@router.delete(
    "/admin/doctors/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_doctor(
    doctor_id: int,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> None:
    try:
        await DeleteDoctorUseCase(repo).execute(doctor_id)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


@router.patch(
    "/admin/doctors/{doctor_id}/availability",
    response_model=DoctorSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_toggle_availability(
    doctor_id: int,
    body: DoctorAvailabilitySchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await ToggleDoctorAvailabilityUseCase(repo).execute(
            doctor_id, body.is_available
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


# ── Admin — Sessions médecin ──────────────────────────────────────────────────

@router.get(
    "/admin/doctors/{doctor_id}/sessions",
    response_model=list[DoctorSessionSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_sessions(
    doctor_id: int,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> list[DoctorSessionSchema]:
    sessions = await ListDoctorSessionsUseCase(repo).execute(doctor_id)
    return [DoctorSessionSchema.model_validate(s.__dict__) for s in sessions]


@router.post(
    "/admin/doctors/{doctor_id}/sessions",
    response_model=DoctorSessionSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_session(
    doctor_id: int,
    body: DoctorSessionCreateSchema,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> DoctorSessionSchema:
    session = await CreateDoctorSessionUseCase(repo).execute(
        doctor_id=doctor_id, day_of_week=body.day_of_week,
        start_time=body.start_time, end_time=body.end_time,
        slot_duration_minutes=body.slot_duration_minutes,
        max_patients_per_slot=body.max_patients_per_slot,
    )
    return DoctorSessionSchema.model_validate(session.__dict__)


@router.put(
    "/admin/doctors/{doctor_id}/sessions/{session_id}",
    response_model=DoctorSessionSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_session(
    doctor_id: int,
    session_id: int,
    body: DoctorSessionUpdateSchema,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> DoctorSessionSchema:
    try:
        session = await UpdateDoctorSessionUseCase(repo).execute(
            session_id,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except DoctorSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSessionSchema.model_validate(session.__dict__)


@router.delete(
    "/admin/doctors/{doctor_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_session(
    doctor_id: int,
    session_id: int,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> None:
    try:
        await DeleteDoctorSessionUseCase(repo).execute(session_id)
    except DoctorSessionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Congés médecin ────────────────────────────────────────────────────

@router.get(
    "/admin/doctors/{doctor_id}/leaves",
    response_model=list[DoctorLeaveSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_leaves(
    doctor_id: int,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> list[DoctorLeaveSchema]:
    leaves = await ListDoctorLeavesUseCase(repo).execute(doctor_id)
    return [DoctorLeaveSchema.model_validate(l.__dict__) for l in leaves]


@router.post(
    "/admin/doctors/{doctor_id}/leaves",
    response_model=DoctorLeaveSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_leave(
    doctor_id: int,
    body: DoctorLeaveCreateSchema,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> DoctorLeaveSchema:
    leave = await CreateDoctorLeaveUseCase(repo).execute(
        doctor_id=doctor_id, leave_date=body.leave_date,
        reason=body.reason, is_full_day=body.is_full_day,
        start_time=body.start_time, end_time=body.end_time,
    )
    return DoctorLeaveSchema.model_validate(leave.__dict__)


@router.delete(
    "/admin/doctors/{doctor_id}/leaves/{leave_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_leave(
    doctor_id: int,
    leave_id: int,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> None:
    try:
        await DeleteDoctorLeaveUseCase(repo).execute(leave_id)
    except DoctorLeaveNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Receptionists ─────────────────────────────────────────────────────

@router.post(
    "/admin/clinics/{clinic_id}/receptionists",
    response_model=ReceptionistSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_receptionist(
    clinic_id: int,
    body: ReceptionistCreateSchema,
    repo: SQLReceptionistRepository = Depends(_receptionist_repo),
) -> ReceptionistSchema:
    rec = await CreateReceptionistUseCase(repo).execute(
        user_id=body.user_id, clinic_id=clinic_id,
    )
    return ReceptionistSchema.model_validate(rec.__dict__)


@router.delete(
    "/admin/receptionists/{receptionist_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_receptionist(
    receptionist_id: int,
    repo: SQLReceptionistRepository = Depends(_receptionist_repo),
) -> None:
    try:
        await DeleteReceptionistUseCase(repo).execute(receptionist_id)
    except ReceptionistNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Modération avis ───────────────────────────────────────────────────

@router.get(
    "/admin/doctor-ratings",
    response_model=Page[DoctorRatingSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_pending_ratings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> Page[DoctorRatingSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListPendingRatingsUseCase(repo).execute(params)
    return Page[DoctorRatingSchema](
        data=[DoctorRatingSchema.model_validate(r.__dict__) for r in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.patch(
    "/admin/doctor-ratings/{rating_id}/approve",
    response_model=DoctorRatingSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_approve_rating(
    rating_id: int,
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> DoctorRatingSchema:
    try:
        rating = await ApproveRatingUseCase(repo).execute(rating_id)
    except DoctorRatingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorRatingSchema.model_validate(rating.__dict__)


@router.delete(
    "/admin/doctor-ratings/{rating_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_rating(
    rating_id: int,
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> None:
    try:
        await DeleteRatingUseCase(repo).execute(rating_id)
    except DoctorRatingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
