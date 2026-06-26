from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.clinic.domain.entites import (
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
        id_ville: Optional[int] = None,
        id_categorie: Optional[int] = None,
        search: Optional[str] = None,
        est_mis_en_avant: Optional[bool] = None,
    ) -> tuple[list[Clinic], int]:
        ...

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def get_by_id(self, id_clinique: int) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def create(
        self,
        id_proprietaire: int,
        nom: str,
        identifiant_url: str,
        description: Optional[str] = None,
        adresse: Optional[str] = None,
        id_ville: Optional[int] = None,
        telephone: Optional[str] = None,
        courriel: Optional[str] = None,
        site_web: Optional[str] = None,
        logo: Optional[str] = None,
        image_couverture: Optional[str] = None,
        latitude: Optional[Decimal] = None,
        longitude: Optional[Decimal] = None,
        taux_commission: Decimal = Decimal("0"),
    ) -> Clinic:
        ...

    @abstractmethod
    async def update(self, id_clinique: int, **kwargs) -> Optional[Clinic]:
        ...

    @abstractmethod
    async def soft_delete(self, id_clinique: int) -> bool:
        ...

    @abstractmethod
    async def slug_exists(self, identifiant_url: str, exclude_id: Optional[int] = None) -> bool:
        ...


class AbstractClinicCategoryRepository(ABC):
    @abstractmethod
    async def list_active(self) -> list[ClinicCategory]:
        ...

    @abstractmethod
    async def get_by_id(self, id_categorie: int) -> Optional[ClinicCategory]:
        ...

    @abstractmethod
    async def create(
        self,
        nom: str,
        identifiant_url: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ClinicCategory:
        ...

    @abstractmethod
    async def update(self, id_categorie: int, **kwargs) -> Optional[ClinicCategory]:
        ...

    @abstractmethod
    async def soft_delete(self, id_categorie: int) -> bool:
        ...


class AbstractClinicServiceRepository(ABC):
    @abstractmethod
    async def list_by_clinic(self, id_clinique: int) -> list[ClinicService]:
        ...

    @abstractmethod
    async def get_by_id(self, id_service: int) -> Optional[ClinicService]:
        ...

    @abstractmethod
    async def create(
        self,
        id_clinique: int,
        nom: str,
        description: Optional[str] = None,
        prix: Decimal = Decimal("0"),
        duree_minutes: int = 30,
    ) -> ClinicService:
        ...

    @abstractmethod
    async def update(self, id_service: int, **kwargs) -> Optional[ClinicService]:
        ...

    @abstractmethod
    async def soft_delete(self, id_service: int) -> bool:
        ...


class AbstractDoctorRepository(ABC):
    @abstractmethod
    async def list_paginated(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        specialite: Optional[str] = None,
        id_ville: Optional[int] = None,
        min_fee: Optional[Decimal] = None,
        max_fee: Optional[Decimal] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Doctor], int]:
        ...

    @abstractmethod
    async def get_by_id(self, id_medecin: int) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def create(
        self,
        id_utilisateur: int,
        id_clinique: int,
        specialite: Optional[str] = None,
        qualification: Optional[str] = None,
        annees_experience: int = 0,
        honoraires_consultation: Decimal = Decimal("0"),
        montant_avance: Decimal = Decimal("0"),
    ) -> Doctor:
        ...

    @abstractmethod
    async def update(self, id_medecin: int, **kwargs) -> Optional[Doctor]:
        ...

    @abstractmethod
    async def soft_delete(self, id_medecin: int) -> bool:
        ...

    @abstractmethod
    async def find_active_session(
        self, id_medecin: int, jour_semaine: int
    ) -> Optional[DoctorSession]:
        ...

    @abstractmethod
    async def find_leave(
        self, id_medecin: int, date_absence: date
    ) -> Optional[DoctorLeave]:
        ...

    @abstractmethod
    async def count_booked_slots(
        self, id_medecin: int, slot_date: date
    ) -> dict[str, int]:
        """Retourne dict[slot_start_iso, count] des rendez-vous confirmés/pending."""
        ...

    @abstractmethod
    async def get_average_rating(self, id_medecin: int) -> Optional[float]:
        ...


class AbstractDoctorSessionRepository(ABC):
    @abstractmethod
    async def list_by_doctor(self, id_medecin: int) -> list[DoctorSession]:
        ...

    @abstractmethod
    async def get_by_id(self, session_id: int) -> Optional[DoctorSession]:
        ...

    @abstractmethod
    async def create(
        self,
        id_medecin: int,
        jour_semaine: int,
        heure_debut,
        heure_fin,
        duree_creneau_minutes: int = 30,
        max_patients_par_creneau: int = 1,
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
    async def list_by_doctor(self, id_medecin: int) -> list[DoctorLeave]:
        ...

    @abstractmethod
    async def get_by_id(self, leave_id: int) -> Optional[DoctorLeave]:
        ...

    @abstractmethod
    async def create(
        self,
        id_medecin: int,
        date_absence: date,
        motif: Optional[str] = None,
        journee_complete: bool = True,
        heure_debut=None,
        heure_fin=None,
    ) -> DoctorLeave:
        ...

    @abstractmethod
    async def delete(self, leave_id: int) -> bool:
        ...


class AbstractDoctorRatingRepository(ABC):
    @abstractmethod
    async def list_approved_by_doctor(
        self, id_medecin: int, params: PaginationParams
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
    async def user_already_rated(self, id_medecin: int, id_utilisateur: int) -> bool:
        ...

    @abstractmethod
    async def create(
        self,
        id_medecin: int,
        id_utilisateur: int,
        note: int,
        commentaire: Optional[str] = None,
        id_rendez_vous: Optional[int] = None,
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
    async def create(self, id_utilisateur: int, id_clinique: int) -> Receptionist:
        ...

    @abstractmethod
    async def soft_delete(self, receptionist_id: int) -> bool:
        ...
