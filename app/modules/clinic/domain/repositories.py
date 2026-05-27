from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

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
from app.shared.schemas.pagination import PaginationParams


class AbstractClinicRepository(ABC):
    @abstractmethod
    async def list_paginated(
        self,
        params: PaginationParams,
        city_id: Optional[int] = None,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        is_featured: Optional[bool] = None,
    ) -> tuple[list[Clinic], int]:
        ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def get_by_id(self, clinic_id: int) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def create(
        self,
        owner_id: int,
        name: str,
        slug: str,
        description: Optional[str] = None,
        address: Optional[str] = None,
        city_id: Optional[int] = None,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        logo: Optional[str] = None,
        cover_image: Optional[str] = None,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        commission_rate: Decimal = Decimal("0"),
    ) -> Clinic:
        ...

    @abstractmethod
    async def update(self, clinic_id: int, **kwargs) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def soft_delete(self, clinic_id: int) -> bool:
        ...

    @abstractmethod
    async def slug_exists(self, slug: str, exclude_id: Optional[int] = None) -> bool:
        ...


class AbstractClinicCategoryRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[ClinicCategory]:
        ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Optional[ClinicCategory]:
        ...

    @abstractmethod
    async def create(
        self,
        name: str,
        slug: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ClinicCategory:
        ...

    @abstractmethod
    async def update(self, category_id: int, **kwargs) -> Optional[ClinicCategory]:
        ...

    @abstractmethod
    async def soft_delete(self, category_id: int) -> bool:
        ...


class AbstractClinicServiceRepository(ABC):
    @abstractmethod
    async def list_by_clinic(self, clinic_id: int) -> list[ClinicService]:
        ...

    @abstractmethod
    async def get_by_id(self, service_id: int) -> Optional[ClinicService]:
        ...

    @abstractmethod
    async def create(
        self,
        clinic_id: int,
        name: str,
        description: Optional[str] = None,
        price: Decimal = Decimal("0"),
        duration_minutes: int = 30,
    ) -> ClinicService:
        ...

    @abstractmethod
    async def update(self, service_id: int, **kwargs) -> Optional[ClinicService]:
        ...

    @abstractmethod
    async def soft_delete(self, service_id: int) -> bool:
        ...


class AbstractDoctorRepository(ABC):
    @abstractmethod
    async def list_paginated(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        speciality: Optional[str] = None,
        city_id: Optional[int] = None,
        min_fee: Optional[Decimal] = None,
        max_fee: Optional[Decimal] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Doctor], int]:
        ...

    @abstractmethod
    async def get_by_id(self, doctor_id: int) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def create(
        self,
        user_id: int,
        clinic_id: int,
        speciality: Optional[str] = None,
        qualification: Optional[str] = None,
        experience_years: int = 0,
        consultation_fee: Decimal = Decimal("0"),
        advance_payment_amount: Decimal = Decimal("0"),
    ) -> Doctor:
        ...

    @abstractmethod
    async def update(self, doctor_id: int, **kwargs) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def soft_delete(self, doctor_id: int) -> bool:
        ...

    @abstractmethod
    async def find_active_session(
        self, doctor_id: int, day_of_week: int
    ) -> Optional[DoctorSession]:
        ...

    @abstractmethod
    async def find_leave(
        self, doctor_id: int, leave_date: date
    ) -> Optional[DoctorLeave]:
        ...

    @abstractmethod
    async def count_booked_slots(
        self, doctor_id: int, slot_date: date
    ) -> dict[str, int]:
        """Retourne dict[slot_start_iso, count] des rendez-vous confirmés/pending."""
        ...

    @abstractmethod
    async def get_average_rating(self, doctor_id: int) -> Optional[float]:
        ...


class AbstractDoctorSessionRepository(ABC):
    @abstractmethod
    async def list_by_doctor(self, doctor_id: int) -> list[DoctorSession]:
        ...

    @abstractmethod
    async def get_by_id(self, session_id: int) -> Optional[DoctorSession]:
        ...

    @abstractmethod
    async def create(
        self,
        doctor_id: int,
        day_of_week: int,
        start_time,
        end_time,
        slot_duration_minutes: int = 30,
        max_patients_per_slot: int = 1,
    ) -> DoctorSession:
        ...

    @abstractmethod
    async def update(self, session_id: int, **kwargs) -> Optional[DoctorSession]:
        ...

    @abstractmethod
    async def delete(self, session_id: int) -> bool:
        ...


class AbstractDoctorLeaveRepository(ABC):
    @abstractmethod
    async def list_by_doctor(self, doctor_id: int) -> list[DoctorLeave]:
        ...

    @abstractmethod
    async def get_by_id(self, leave_id: int) -> Optional[DoctorLeave]:
        ...

    @abstractmethod
    async def create(
        self,
        doctor_id: int,
        leave_date: date,
        reason: Optional[str] = None,
        is_full_day: bool = True,
        start_time=None,
        end_time=None,
    ) -> DoctorLeave:
        ...

    @abstractmethod
    async def delete(self, leave_id: int) -> bool:
        ...


class AbstractDoctorRatingRepository(ABC):
    @abstractmethod
    async def list_approved_by_doctor(
        self, doctor_id: int, params: PaginationParams
    ) -> tuple[list[DoctorRating], int]:
        ...

    @abstractmethod
    async def list_pending(
        self, params: PaginationParams
    ) -> tuple[list[DoctorRating], int]:
        ...

    @abstractmethod
    async def get_by_id(self, rating_id: int) -> Optional[DoctorRating]:
        ...

    @abstractmethod
    async def user_already_rated(self, doctor_id: int, user_id: int) -> bool:
        ...

    @abstractmethod
    async def create(
        self,
        doctor_id: int,
        user_id: int,
        rating: int,
        comment: Optional[str] = None,
        appointment_id: Optional[int] = None,
    ) -> DoctorRating:
        ...

    @abstractmethod
    async def approve(self, rating_id: int) -> Optional[DoctorRating]:
        ...

    @abstractmethod
    async def soft_delete(self, rating_id: int) -> bool:
        ...


class AbstractReceptionistRepository(ABC):
    @abstractmethod
    async def get_by_id(self, receptionist_id: int) -> Optional[Receptionist]:
        ...

    @abstractmethod
    async def create(self, user_id: int, clinic_id: int) -> Receptionist:
        ...

    @abstractmethod
    async def soft_delete(self, receptionist_id: int) -> bool:
        ...
