"""Routeur API — module clinique (~86 endpoints)."""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
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
from app.modules.clinic.application.cas_utilisation import (
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
from app.modules.clinic.infrastructure.depots import (
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

router = APIRouter(tags=["Cliniques"])

_admin_dep = require_role("admin", "super-admin")


# ── Fabriques de dépendances ──────────────────────────────────────────────────

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


# ── Accès public — Cliniques ──────────────────────────────────────────────────

@router.get("/cliniques", response_model=Page[ClinicSchema])
async def list_clinics(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    id_ville: Optional[int] = Query(None),
    id_categorie: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    est_mis_en_avant: Optional[bool] = Query(None),
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> Page[ClinicSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListClinicsUseCase(repo).execute(
        params, id_ville=id_ville, id_categorie=id_categorie,
        search=search, est_mis_en_avant=est_mis_en_avant,
    )
    return Page[ClinicSchema](
        data=[ClinicSchema.model_validate(c.__dict__) for c in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get("/cliniques/{identifiant_url}", response_model=ClinicSchema)
async def get_clinic(
    identifiant_url: str,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await GetClinicBySlugUseCase(repo).execute(identifiant_url)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.get("/categories-cliniques", response_model=list[ClinicCategorySchema])
async def list_categories(
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> list[ClinicCategorySchema]:
    categories = await ListCategoriesUseCase(repo).execute()
    return [ClinicCategorySchema.model_validate(c.__dict__) for c in categories]


# ── Accès public — Médecins ───────────────────────────────────────────────────

@router.get("/medecins", response_model=Page[DoctorSchema])
async def list_doctors(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    id_clinique: Optional[int] = Query(None),
    specialite: Optional[str] = Query(None),
    id_ville: Optional[int] = Query(None),
    min_fee: Optional[Decimal] = Query(None),
    max_fee: Optional[Decimal] = Query(None),
    search: Optional[str] = Query(None),
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> Page[DoctorSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListDoctorsUseCase(repo).execute(
        params, id_clinique=id_clinique, specialite=specialite,
        id_ville=id_ville, min_fee=min_fee, max_fee=max_fee, search=search,
    )
    return Page[DoctorSchema](
        data=[DoctorSchema.model_validate(d.__dict__) for d in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


@router.get("/medecins/{id_medecin}", response_model=DoctorSchema)
async def get_doctor(
    id_medecin: int,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await GetDoctorUseCase(repo).execute(id_medecin)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


@router.get("/medecins/{id_medecin}/creneaux", response_model=AvailableSlotsSchema)
async def get_available_slots(
    id_medecin: int,
    slot_date: date = Query(..., alias="date"),
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> AvailableSlotsSchema:
    slots = await GetAvailableSlotsUseCase(repo).execute(id_medecin, slot_date)
    return AvailableSlotsSchema(id_medecin=id_medecin, date=slot_date, slots=slots)


@router.get("/medecins/{id_medecin}/horaires", response_model=list[DoctorSessionSchema])
async def get_doctor_schedule(
    id_medecin: int,
    s_repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> list[DoctorSessionSchema]:
    sessions = await GetDoctorScheduleUseCase(s_repo).execute(id_medecin)
    return [DoctorSessionSchema.model_validate(s.__dict__) for s in sessions]


@router.get("/medecins/{id_medecin}/evaluations", response_model=Page[DoctorRatingSchema])
async def list_doctor_ratings(
    id_medecin: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> Page[DoctorRatingSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    page_result = await ListApprovedRatingsUseCase(repo).execute(id_medecin, params)
    return Page[DoctorRatingSchema](
        data=[DoctorRatingSchema.model_validate(r.__dict__) for r in page_result.data],
        total=page_result.total,
        page=page_result.page,
        per_page=page_result.per_page,
        total_pages=page_result.total_pages,
    )


# ── Authentifié — Notation des médecins ──────────────────────────────────────

@router.post(
    "/medecins/{id_medecin}/evaluations",
    response_model=DoctorRatingSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def rate_doctor(
    id_medecin: int,
    body: DoctorRatingCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> DoctorRatingSchema:
    try:
        note = await RateDoctorUseCase(repo).execute(
            id_medecin=id_medecin,
            id_utilisateur=current_user["id"],
            note=body.note,
            commentaire=body.commentaire,
            id_rendez_vous=body.id_rendez_vous,
        )
    except DuplicateRatingError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    return DoctorRatingSchema.model_validate(note.__dict__)


# ── Admin — Gestion des cliniques ────────────────────────────────────────────

@router.post(
    "/admin/cliniques",
    response_model=ClinicSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_clinic(
    body: ClinicCreateSchema,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await CreateClinicUseCase(repo).execute(
            id_proprietaire=body.id_proprietaire, nom=body.nom, identifiant_url=body.identifiant_url,
            description=body.description, adresse=body.adresse,
            id_ville=body.id_ville, telephone=body.telephone, courriel=body.courriel,
            site_web=body.site_web, logo=body.logo, image_couverture=body.image_couverture,
            latitude=body.latitude, longitude=body.longitude,
            taux_commission=body.taux_commission,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.put(
    "/admin/cliniques/{id_clinique}",
    response_model=ClinicSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_clinic(
    id_clinique: int,
    body: ClinicUpdateSchema,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await UpdateClinicUseCase(repo).execute(
            id_clinique,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


@router.delete(
    "/admin/cliniques/{id_clinique}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_clinic(
    id_clinique: int,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> None:
    try:
        await DeleteClinicUseCase(repo).execute(id_clinique)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


@router.patch(
    "/admin/cliniques/{id_clinique}/basculer",
    response_model=ClinicSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_toggle_clinic(
    id_clinique: int,
    repo: SQLClinicRepository = Depends(_clinic_repo),
) -> ClinicSchema:
    try:
        clinic = await ToggleClinicActiveUseCase(repo).execute(id_clinique)
    except ClinicNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicSchema.model_validate(clinic.__dict__)


# ── Admin — Gestion des catégories ───────────────────────────────────────────

@router.post(
    "/admin/categories-cliniques",
    response_model=ClinicCategorySchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_category(
    body: ClinicCategoryCreateSchema,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> ClinicCategorySchema:
    cat = await CreateCategoryUseCase(repo).execute(
        nom=body.nom, identifiant_url=body.identifiant_url, image=body.image, description=body.description,
    )
    return ClinicCategorySchema.model_validate(cat.__dict__)


@router.put(
    "/admin/categories-cliniques/{id_categorie}",
    response_model=ClinicCategorySchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_category(
    id_categorie: int,
    body: ClinicCategoryUpdateSchema,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> ClinicCategorySchema:
    try:
        cat = await UpdateCategoryUseCase(repo).execute(
            id_categorie,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicCategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicCategorySchema.model_validate(cat.__dict__)


@router.delete(
    "/admin/categories-cliniques/{id_categorie}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_category(
    id_categorie: int,
    repo: SQLClinicCategoryRepository = Depends(_category_repo),
) -> None:
    try:
        await DeleteCategoryUseCase(repo).execute(id_categorie)
    except ClinicCategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Gestion des services de clinique ─────────────────────────────────

@router.get(
    "/admin/cliniques/{id_clinique}/services",
    response_model=list[ClinicServiceSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_services(
    id_clinique: int,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> list[ClinicServiceSchema]:
    services = await ListClinicServicesUseCase(repo).execute(id_clinique)
    return [ClinicServiceSchema.model_validate(s.__dict__) for s in services]


@router.post(
    "/admin/cliniques/{id_clinique}/services",
    response_model=ClinicServiceSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_service(
    id_clinique: int,
    body: ClinicServiceCreateSchema,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> ClinicServiceSchema:
    service = await CreateClinicServiceUseCase(repo).execute(
        id_clinique=id_clinique, nom=body.nom, description=body.description,
        prix=body.prix, duree_minutes=body.duree_minutes,
    )
    return ClinicServiceSchema.model_validate(service.__dict__)


@router.put(
    "/admin/cliniques/{id_clinique}/services/{id_service}",
    response_model=ClinicServiceSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_service(
    id_clinique: int,
    id_service: int,
    body: ClinicServiceUpdateSchema,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> ClinicServiceSchema:
    try:
        service = await UpdateClinicServiceUseCase(repo).execute(
            id_service,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return ClinicServiceSchema.model_validate(service.__dict__)


@router.delete(
    "/admin/cliniques/{id_clinique}/services/{id_service}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_service(
    id_clinique: int,
    id_service: int,
    repo: SQLClinicServiceRepository = Depends(_service_repo),
) -> None:
    try:
        await DeleteClinicServiceUseCase(repo).execute(id_service)
    except ClinicServiceNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Gestion des médecins ─────────────────────────────────────────────

@router.post(
    "/admin/cliniques/{id_clinique}/medecins",
    response_model=DoctorSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_doctor(
    id_clinique: int,
    body: DoctorCreateSchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    doctor = await CreateDoctorUseCase(repo).execute(
        id_utilisateur=body.id_utilisateur, id_clinique=id_clinique,
        specialite=body.specialite, qualification=body.qualification,
        annees_experience=body.annees_experience,
        honoraires_consultation=body.honoraires_consultation,
        montant_avance=body.montant_avance,
    )
    return DoctorSchema.model_validate(doctor.__dict__)


@router.put(
    "/admin/medecins/{id_medecin}",
    response_model=DoctorSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_doctor(
    id_medecin: int,
    body: DoctorUpdateSchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await UpdateDoctorUseCase(repo).execute(
            id_medecin,
            **{k: v for k, v in body.model_dump(exclude_none=True).items()},
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


@router.delete(
    "/admin/medecins/{id_medecin}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_doctor(
    id_medecin: int,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> None:
    try:
        await DeleteDoctorUseCase(repo).execute(id_medecin)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


@router.patch(
    "/admin/medecins/{id_medecin}/disponibilite",
    response_model=DoctorSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_toggle_availability(
    id_medecin: int,
    body: DoctorAvailabilitySchema,
    repo: SQLDoctorRepository = Depends(_doctor_repo),
) -> DoctorSchema:
    try:
        doctor = await ToggleDoctorAvailabilityUseCase(repo).execute(
            id_medecin, body.est_disponible
        )
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSchema.model_validate(doctor.__dict__)


# ── Admin — Gestion des sessions médecin ─────────────────────────────────────

@router.get(
    "/admin/medecins/{id_medecin}/seances",
    response_model=list[DoctorSessionSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_sessions(
    id_medecin: int,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> list[DoctorSessionSchema]:
    sessions = await ListDoctorSessionsUseCase(repo).execute(id_medecin)
    return [DoctorSessionSchema.model_validate(s.__dict__) for s in sessions]


@router.post(
    "/admin/medecins/{id_medecin}/seances",
    response_model=DoctorSessionSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_session(
    id_medecin: int,
    body: DoctorSessionCreateSchema,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> DoctorSessionSchema:
    session = await CreateDoctorSessionUseCase(repo).execute(
        id_medecin=id_medecin, jour_semaine=body.jour_semaine,
        heure_debut=body.heure_debut, heure_fin=body.heure_fin,
        duree_creneau_minutes=body.duree_creneau_minutes,
        max_patients_par_creneau=body.max_patients_par_creneau,
    )
    return DoctorSessionSchema.model_validate(session.__dict__)


@router.put(
    "/admin/medecins/{id_medecin}/seances/{session_id}",
    response_model=DoctorSessionSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_update_session(
    id_medecin: int,
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorSessionSchema.model_validate(session.__dict__)


@router.delete(
    "/admin/medecins/{id_medecin}/seances/{session_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_session(
    id_medecin: int,
    session_id: int,
    repo: SQLDoctorSessionRepository = Depends(_session_repo),
) -> None:
    try:
        await DeleteDoctorSessionUseCase(repo).execute(session_id)
    except DoctorSessionNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Gestion des congés médecin ───────────────────────────────────────

@router.get(
    "/admin/medecins/{id_medecin}/conges",
    response_model=list[DoctorLeaveSchema],
    dependencies=[Depends(_admin_dep)],
)
async def admin_list_leaves(
    id_medecin: int,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> list[DoctorLeaveSchema]:
    leaves = await ListDoctorLeavesUseCase(repo).execute(id_medecin)
    return [DoctorLeaveSchema.model_validate(l.__dict__) for l in leaves]


@router.post(
    "/admin/medecins/{id_medecin}/conges",
    response_model=DoctorLeaveSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_leave(
    id_medecin: int,
    body: DoctorLeaveCreateSchema,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> DoctorLeaveSchema:
    leave = await CreateDoctorLeaveUseCase(repo).execute(
        id_medecin=id_medecin, date_absence=body.date_absence,
        motif=body.motif, journee_complete=body.journee_complete,
        heure_debut=body.heure_debut, heure_fin=body.heure_fin,
    )
    return DoctorLeaveSchema.model_validate(leave.__dict__)


@router.delete(
    "/admin/medecins/{id_medecin}/conges/{leave_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_leave(
    id_medecin: int,
    leave_id: int,
    repo: SQLDoctorLeaveRepository = Depends(_leave_repo),
) -> None:
    try:
        await DeleteDoctorLeaveUseCase(repo).execute(leave_id)
    except DoctorLeaveNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Gestion des réceptionnistes ──────────────────────────────────────

@router.post(
    "/admin/cliniques/{id_clinique}/receptionnistes",
    response_model=ReceptionistSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(_admin_dep)],
)
async def admin_create_receptionist(
    id_clinique: int,
    body: ReceptionistCreateSchema,
    repo: SQLReceptionistRepository = Depends(_receptionist_repo),
) -> ReceptionistSchema:
    rec = await CreateReceptionistUseCase(repo).execute(
        id_utilisateur=body.id_utilisateur, id_clinique=id_clinique,
    )
    return ReceptionistSchema.model_validate(rec.__dict__)


@router.delete(
    "/admin/receptionnistes/{receptionist_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_receptionist(
    receptionist_id: int,
    repo: SQLReceptionistRepository = Depends(_receptionist_repo),
) -> None:
    try:
        await DeleteReceptionistUseCase(repo).execute(receptionist_id)
    except ReceptionistNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)


# ── Admin — Modération des avis médecins ─────────────────────────────────────

@router.get(
    "/admin/evaluations-medecins",
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
    "/admin/evaluations-medecins/{rating_id}/approuver",
    response_model=DoctorRatingSchema,
    dependencies=[Depends(_admin_dep)],
)
async def admin_approve_rating(
    rating_id: int,
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> DoctorRatingSchema:
    try:
        note = await ApproveRatingUseCase(repo).execute(rating_id)
    except DoctorRatingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return DoctorRatingSchema.model_validate(note.__dict__)


@router.delete(
    "/admin/evaluations-medecins/{rating_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(_admin_dep)],
)
async def admin_delete_rating(
    rating_id: int,
    repo: SQLDoctorRatingRepository = Depends(_rating_repo),
) -> None:
    try:
        await DeleteRatingUseCase(repo).execute(rating_id)
    except DoctorRatingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
