"""Use cases — module clinic."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from app.modules.clinic.domain.entities import (
    Clinic,
    ClinicCategory,
    ClinicService,
    Doctor,
    DoctorLeave,
    DoctorRating,
    DoctorSession,
    Receptionist,
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
from app.modules.clinic.domain.repositories import (
    AbstractClinicCategoryRepository,
    AbstractClinicRepository,
    AbstractClinicServiceRepository,
    AbstractDoctorLeaveRepository,
    AbstractDoctorRatingRepository,
    AbstractDoctorRepository,
    AbstractDoctorSessionRepository,
    AbstractReceptionistRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


# ── Clinic ────────────────────────────────────────────────────────────────────

class ListClinicsUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
    ) -> Page[Clinic]:
        data, total = await self._repo.list_paginated(
            params, city_id=city_id, category_id=category_id,
            search=search, is_featured=is_featured,
        )
        return Page.create(data, total, params)


class GetClinicBySlugUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> Clinic:
        clinic = await self._repo.get_by_slug(slug)
        if clinic is None:
            raise ClinicNotFoundError(slug)
        return clinic


class CreateClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        owner_id: int,
        name: str,
        slug: str,
        **kwargs: Any,
    ) -> Clinic:
        if await self._repo.slug_exists(slug):
            raise SlugAlreadyExistsError(slug)
        return await self._repo.create(owner_id=owner_id, name=name, slug=slug, **kwargs)


class UpdateClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, clinic_id: int, **kwargs: Any) -> Clinic:
        slug = kwargs.get("slug")
        if slug and await self._repo.slug_exists(slug, exclude_id=clinic_id):
            raise SlugAlreadyExistsError(slug)
        updated = await self._repo.update(clinic_id, **kwargs)
        if updated is None:
            raise ClinicNotFoundError(clinic_id)
        return updated


class DeleteClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, clinic_id: int) -> None:
        deleted = await self._repo.soft_delete(clinic_id)
        if not deleted:
            raise ClinicNotFoundError(clinic_id)


class ToggleClinicActiveUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, clinic_id: int) -> Clinic:
        clinic = await self._repo.get_by_id(clinic_id)
        if clinic is None:
            raise ClinicNotFoundError(clinic_id)
        clinic.toggle_active()
        updated = await self._repo.update(clinic_id, is_active=clinic.is_active)
        if updated is None:
            raise ClinicNotFoundError(clinic_id)
        return updated


# ── ClinicCategory ────────────────────────────────────────────────────────────

class ListCategoriesUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(self) -> list[ClinicCategory]:
        return await self._repo.list_active()


class CreateCategoryUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        slug: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ClinicCategory:
        return await self._repo.create(name=name, slug=slug, image=image, description=description)


class UpdateCategoryUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, category_id: int, **kwargs: Any) -> ClinicCategory:
        updated = await self._repo.update(category_id, **kwargs)
        if updated is None:
            raise ClinicCategoryNotFoundError(category_id)
        return updated


class DeleteCategoryUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, category_id: int) -> None:
        deleted = await self._repo.soft_delete(category_id)
        if not deleted:
            raise ClinicCategoryNotFoundError(category_id)


# ── ClinicService ─────────────────────────────────────────────────────────────

class ListClinicServicesUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, clinic_id: int) -> list[ClinicService]:
        return await self._repo.list_by_clinic(clinic_id)


class CreateClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        clinic_id: int,
        name: str,
        description: Optional[str] = None,
        price: Decimal = Decimal("0"),
        duration_minutes: int = 30,
    ) -> ClinicService:
        return await self._repo.create(
            clinic_id=clinic_id, name=name,
            description=description, price=price,
            duration_minutes=duration_minutes,
        )


class UpdateClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int, **kwargs: Any) -> ClinicService:
        updated = await self._repo.update(service_id, **kwargs)
        if updated is None:
            raise ClinicServiceNotFoundError(service_id)
        return updated


class DeleteClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int) -> None:
        deleted = await self._repo.soft_delete(service_id)
        if not deleted:
            raise ClinicServiceNotFoundError(service_id)


# ── Doctor ────────────────────────────────────────────────────────────────────

class ListDoctorsUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        speciality: Optional[str] = None,
        city_id: Optional[int] = None,
        min_fee: Optional[Decimal] = None,
        max_fee: Optional[Decimal] = None,
        search: Optional[str] = None,
    ) -> Page[Doctor]:
        data, total = await self._repo.list_paginated(
            params, clinic_id=clinic_id, speciality=speciality,
            city_id=city_id, min_fee=min_fee, max_fee=max_fee, search=search,
        )
        return Page.create(data, total, params)


class GetDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int) -> Doctor:
        doctor = await self._repo.get_by_id(doctor_id)
        if doctor is None:
            raise DoctorNotFoundError(doctor_id)
        return doctor


class GetAvailableSlotsUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int, for_date: date) -> list[datetime]:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Vérifier que la date n'est pas dans le passé
        if for_date < now.date():
            return []

        # 2. Trouver la session active pour ce jour de semaine (0=Lundi)
        day_of_week = for_date.weekday()  # Python: 0=Lundi
        session = await self._repo.find_active_session(doctor_id, day_of_week)
        if not session:
            return []

        # 3. Vérifier qu'il n'y a pas de congé ce jour
        leave = await self._repo.find_leave(doctor_id, for_date)
        if leave and leave.is_full_day:
            return []

        # 4. Générer les créneaux théoriques
        theoretical = session.generate_theoretical_slots(for_date)

        # 5. Exclure les créneaux passés (si date = aujourd'hui)
        if for_date == now.date():
            theoretical = [s for s in theoretical if s > now]

        # 6. Compter les RDV confirmés/pending par créneau
        booked = await self._repo.count_booked_slots(doctor_id, for_date)
        # booked = dict[str, int] — nombre de RDV par créneau (clé = ISO str)

        # 7. Retourner les créneaux où booked_count < max_patients_per_slot
        available = [
            s for s in theoretical
            if booked.get(s.isoformat(), 0) < session.max_patients_per_slot
        ]
        return available


class GetDoctorScheduleUseCase:
    def __init__(self, session_repo: AbstractDoctorSessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, doctor_id: int) -> list[DoctorSession]:
        return await self._session_repo.list_by_doctor(doctor_id)


class CreateDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        user_id: int,
        clinic_id: int,
        speciality: Optional[str] = None,
        qualification: Optional[str] = None,
        experience_years: int = 0,
        consultation_fee: Decimal = Decimal("0"),
        advance_payment_amount: Decimal = Decimal("0"),
    ) -> Doctor:
        return await self._repo.create(
            user_id=user_id, clinic_id=clinic_id,
            speciality=speciality, qualification=qualification,
            experience_years=experience_years,
            consultation_fee=consultation_fee,
            advance_payment_amount=advance_payment_amount,
        )


class UpdateDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int, **kwargs: Any) -> Doctor:
        updated = await self._repo.update(doctor_id, **kwargs)
        if updated is None:
            raise DoctorNotFoundError(doctor_id)
        return updated


class DeleteDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int) -> None:
        deleted = await self._repo.soft_delete(doctor_id)
        if not deleted:
            raise DoctorNotFoundError(doctor_id)


class ToggleDoctorAvailabilityUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int, is_available: bool) -> Doctor:
        updated = await self._repo.update(doctor_id, is_available=is_available)
        if updated is None:
            raise DoctorNotFoundError(doctor_id)
        return updated


# ── DoctorSession ─────────────────────────────────────────────────────────────

class ListDoctorSessionsUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int) -> list[DoctorSession]:
        return await self._repo.list_by_doctor(doctor_id)


class CreateDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: int,
        day_of_week: int,
        start_time,
        end_time,
        slot_duration_minutes: int = 30,
        max_patients_per_slot: int = 1,
    ) -> DoctorSession:
        return await self._repo.create(
            doctor_id=doctor_id, day_of_week=day_of_week,
            start_time=start_time, end_time=end_time,
            slot_duration_minutes=slot_duration_minutes,
            max_patients_per_slot=max_patients_per_slot,
        )


class UpdateDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, session_id: int, **kwargs: Any) -> DoctorSession:
        updated = await self._repo.update(session_id, **kwargs)
        if updated is None:
            raise DoctorSessionNotFoundError(session_id)
        return updated


class DeleteDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, session_id: int) -> None:
        deleted = await self._repo.delete(session_id)
        if not deleted:
            raise DoctorSessionNotFoundError(session_id)


# ── DoctorLeave ───────────────────────────────────────────────────────────────

class ListDoctorLeavesUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(self, doctor_id: int) -> list[DoctorLeave]:
        return await self._repo.list_by_doctor(doctor_id)


class CreateDoctorLeaveUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: int,
        leave_date: date,
        reason: Optional[str] = None,
        is_full_day: bool = True,
        start_time=None,
        end_time=None,
    ) -> DoctorLeave:
        return await self._repo.create(
            doctor_id=doctor_id, leave_date=leave_date,
            reason=reason, is_full_day=is_full_day,
            start_time=start_time, end_time=end_time,
        )


class DeleteDoctorLeaveUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(self, leave_id: int) -> None:
        deleted = await self._repo.delete(leave_id)
        if not deleted:
            raise DoctorLeaveNotFoundError(leave_id)


# ── DoctorRating ──────────────────────────────────────────────────────────────

class ListApprovedRatingsUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(
        self, doctor_id: int, params: PaginationParams
    ) -> Page[DoctorRating]:
        data, total = await self._repo.list_approved_by_doctor(doctor_id, params)
        return Page.create(data, total, params)


class ListPendingRatingsUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[DoctorRating]:
        data, total = await self._repo.list_pending(params)
        return Page.create(data, total, params)


class RateDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        doctor_id: int,
        user_id: int,
        rating: int,
        comment: Optional[str] = None,
        appointment_id: Optional[int] = None,
    ) -> DoctorRating:
        if await self._repo.user_already_rated(doctor_id, user_id):
            raise DuplicateRatingError(doctor_id, user_id)
        return await self._repo.create(
            doctor_id=doctor_id, user_id=user_id,
            rating=rating, comment=comment, appointment_id=appointment_id,
        )


class ApproveRatingUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(self, rating_id: int) -> DoctorRating:
        rating = await self._repo.approve(rating_id)
        if rating is None:
            raise DoctorRatingNotFoundError(rating_id)
        return rating


class DeleteRatingUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(self, rating_id: int) -> None:
        deleted = await self._repo.soft_delete(rating_id)
        if not deleted:
            raise DoctorRatingNotFoundError(rating_id)


# ── Receptionist ──────────────────────────────────────────────────────────────

class CreateReceptionistUseCase:
    def __init__(self, repo: AbstractReceptionistRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: int, clinic_id: int) -> Receptionist:
        return await self._repo.create(user_id=user_id, clinic_id=clinic_id)


class DeleteReceptionistUseCase:
    def __init__(self, repo: AbstractReceptionistRepository) -> None:
        self._repo = repo

    async def execute(self, receptionist_id: int) -> None:
        deleted = await self._repo.soft_delete(receptionist_id)
        if not deleted:
            raise ReceptionistNotFoundError(receptionist_id)
