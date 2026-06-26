"""Cas d'utilisation — module clinique."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional

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
from app.modules.clinic.domain.depots import (
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


# ── Clinique ──────────────────────────────────────────────────────────────────

class ListClinicsUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_ville: Optional[int] = None,
        id_categorie: Optional[int] = None,
        search: Optional[str] = None,
        est_mis_en_avant: Optional[bool] = None,
    ) -> Page[Clinic]:
        data, total = await self._repo.list_paginated(
            params, id_ville=id_ville, id_categorie=id_categorie,
            search=search, est_mis_en_avant=est_mis_en_avant,
        )
        return Page.create(data, total, params)


class GetClinicBySlugUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> Clinic:
        clinic = await self._repo.get_by_slug(identifiant_url)
        if clinic is None:
            raise ClinicNotFoundError(identifiant_url)
        return clinic


class CreateClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_proprietaire: int,
        nom: str,
        identifiant_url: str,
        **kwargs: Any,
    ) -> Clinic:
        if await self._repo.slug_exists(identifiant_url):
            raise SlugAlreadyExistsError(identifiant_url)
        return await self._repo.create(id_proprietaire=id_proprietaire, nom=nom, identifiant_url=identifiant_url, **kwargs)


class UpdateClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, id_clinique: int, **kwargs: Any) -> Clinic:
        identifiant_url = kwargs.get("identifiant_url")
        if identifiant_url and await self._repo.slug_exists(identifiant_url, exclude_id=id_clinique):
            raise SlugAlreadyExistsError(identifiant_url)
        mis_a_jour = await self._repo.update(id_clinique, **kwargs)
        if mis_a_jour is None:
            raise ClinicNotFoundError(id_clinique)
        return mis_a_jour


class DeleteClinicUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, id_clinique: int) -> None:
        supprime = await self._repo.soft_delete(id_clinique)
        if not supprime:
            raise ClinicNotFoundError(id_clinique)


class ToggleClinicActiveUseCase:
    def __init__(self, repo: AbstractClinicRepository) -> None:
        self._repo = repo

    async def execute(self, id_clinique: int) -> Clinic:
        clinique = await self._repo.get_by_id(id_clinique)
        if clinique is None:
            raise ClinicNotFoundError(id_clinique)
        clinique.toggle_active()
        mis_a_jour = await self._repo.update(id_clinique, est_actif=clinique.est_actif)
        if mis_a_jour is None:
            raise ClinicNotFoundError(id_clinique)
        return mis_a_jour


# ── Catégorie de clinique ─────────────────────────────────────────────────────

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
        nom: str,
        identifiant_url: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ClinicCategory:
        return await self._repo.create(nom=nom, identifiant_url=identifiant_url, image=image, description=description)


class UpdateCategoryUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, id_categorie: int, **kwargs: Any) -> ClinicCategory:
        mis_a_jour = await self._repo.update(id_categorie, **kwargs)
        if mis_a_jour is None:
            raise ClinicCategoryNotFoundError(id_categorie)
        return mis_a_jour


class DeleteCategoryUseCase:
    def __init__(self, repo: AbstractClinicCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, id_categorie: int) -> None:
        supprime = await self._repo.soft_delete(id_categorie)
        if not supprime:
            raise ClinicCategoryNotFoundError(id_categorie)


# ── Service de clinique ───────────────────────────────────────────────────────

class ListClinicServicesUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, id_clinique: int) -> list[ClinicService]:
        return await self._repo.list_by_clinic(id_clinique)


class CreateClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_clinique: int,
        nom: str,
        description: Optional[str] = None,
        prix: Decimal = Decimal("0"),
        duree_minutes: int = 30,
    ) -> ClinicService:
        return await self._repo.create(
            id_clinique=id_clinique, nom=nom,
            description=description, prix=prix,
            duree_minutes=duree_minutes,
        )


class UpdateClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, id_service: int, **kwargs: Any) -> ClinicService:
        mis_a_jour = await self._repo.update(id_service, **kwargs)
        if mis_a_jour is None:
            raise ClinicServiceNotFoundError(id_service)
        return mis_a_jour


class DeleteClinicServiceUseCase:
    def __init__(self, repo: AbstractClinicServiceRepository) -> None:
        self._repo = repo

    async def execute(self, id_service: int) -> None:
        supprime = await self._repo.soft_delete(id_service)
        if not supprime:
            raise ClinicServiceNotFoundError(id_service)


# ── Médecin ───────────────────────────────────────────────────────────────────

class ListDoctorsUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        specialite: Optional[str] = None,
        id_ville: Optional[int] = None,
        min_fee: Optional[Decimal] = None,
        max_fee: Optional[Decimal] = None,
        search: Optional[str] = None,
    ) -> Page[Doctor]:
        data, total = await self._repo.list_paginated(
            params, id_clinique=id_clinique, specialite=specialite,
            id_ville=id_ville, min_fee=min_fee, max_fee=max_fee, search=search,
        )
        return Page.create(data, total, params)


class GetDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int) -> Doctor:
        medecin = await self._repo.get_by_id(id_medecin)
        if medecin is None:
            raise DoctorNotFoundError(id_medecin)
        return medecin


class GetAvailableSlotsUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int, for_date: date) -> list[datetime]:
        maintenant = datetime.now(timezone.utc).replace(tzinfo=None)

        # 1. Vérifier que la date n'est pas dans le passé
        if for_date < maintenant.date():
            return []

        # 2. Trouver la session active pour ce jour de semaine (0=Lundi)
        jour_semaine = for_date.weekday()  # Python : 0=Lundi
        session = await self._repo.find_active_session(id_medecin, jour_semaine)
        if not session:
            return []

        # 3. Vérifier qu'il n'y a pas de congé ce jour
        conge = await self._repo.find_leave(id_medecin, for_date)
        if conge and conge.journee_complete:
            return []

        # 4. Générer les créneaux théoriques
        creneaux_theoriques = session.generate_theoretical_slots(for_date)

        # 5. Exclure les créneaux passés (si date = aujourd'hui)
        if for_date == maintenant.date():
            creneaux_theoriques = [c for c in creneaux_theoriques if c > maintenant]

        # 6. Compter les RDV confirmés/en attente par créneau
        reserves = await self._repo.count_booked_slots(id_medecin, for_date)
        # reserves = dict[str, int] — nombre de RDV par créneau (clé = ISO str)

        # 7. Retourner les créneaux où le nombre réservé < max_patients_par_créneau
        disponibles = [
            c for c in creneaux_theoriques
            if reserves.get(c.isoformat(), 0) < session.max_patients_par_creneau
        ]
        return disponibles


class GetDoctorScheduleUseCase:
    def __init__(self, session_repo: AbstractDoctorSessionRepository) -> None:
        self._session_repo = session_repo

    async def execute(self, id_medecin: int) -> list[DoctorSession]:
        return await self._session_repo.list_by_doctor(id_medecin)


class CreateDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_utilisateur: int,
        id_clinique: int,
        specialite: Optional[str] = None,
        qualification: Optional[str] = None,
        annees_experience: int = 0,
        honoraires_consultation: Decimal = Decimal("0"),
        montant_avance: Decimal = Decimal("0"),
    ) -> Doctor:
        return await self._repo.create(
            id_utilisateur=id_utilisateur, id_clinique=id_clinique,
            specialite=specialite, qualification=qualification,
            annees_experience=annees_experience,
            honoraires_consultation=honoraires_consultation,
            montant_avance=montant_avance,
        )


class UpdateDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int, **kwargs: Any) -> Doctor:
        mis_a_jour = await self._repo.update(id_medecin, **kwargs)
        if mis_a_jour is None:
            raise DoctorNotFoundError(id_medecin)
        return mis_a_jour


class DeleteDoctorUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int) -> None:
        supprime = await self._repo.soft_delete(id_medecin)
        if not supprime:
            raise DoctorNotFoundError(id_medecin)


class ToggleDoctorAvailabilityUseCase:
    def __init__(self, repo: AbstractDoctorRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int, est_disponible: bool) -> Doctor:
        mis_a_jour = await self._repo.update(id_medecin, est_disponible=est_disponible)
        if mis_a_jour is None:
            raise DoctorNotFoundError(id_medecin)
        return mis_a_jour


# ── Session médecin ───────────────────────────────────────────────────────────

class ListDoctorSessionsUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int) -> list[DoctorSession]:
        return await self._repo.list_by_doctor(id_medecin)


class CreateDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_medecin: int,
        jour_semaine: int,
        heure_debut,
        heure_fin,
        duree_creneau_minutes: int = 30,
        max_patients_par_creneau: int = 1,
    ) -> DoctorSession:
        return await self._repo.create(
            id_medecin=id_medecin, jour_semaine=jour_semaine,
            heure_debut=heure_debut, heure_fin=heure_fin,
            duree_creneau_minutes=duree_creneau_minutes,
            max_patients_par_creneau=max_patients_par_creneau,
        )


class UpdateDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, session_id: int, **kwargs: Any) -> DoctorSession:
        mis_a_jour = await self._repo.update(session_id, **kwargs)
        if mis_a_jour is None:
            raise DoctorSessionNotFoundError(session_id)
        return mis_a_jour


class DeleteDoctorSessionUseCase:
    def __init__(self, repo: AbstractDoctorSessionRepository) -> None:
        self._repo = repo

    async def execute(self, session_id: int) -> None:
        supprime = await self._repo.delete(session_id)
        if not supprime:
            raise DoctorSessionNotFoundError(session_id)


# ── Congé médecin ─────────────────────────────────────────────────────────────

class ListDoctorLeavesUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(self, id_medecin: int) -> list[DoctorLeave]:
        return await self._repo.list_by_doctor(id_medecin)


class CreateDoctorLeaveUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_medecin: int,
        date_absence: date,
        motif: Optional[str] = None,
        journee_complete: bool = True,
        heure_debut=None,
        heure_fin=None,
    ) -> DoctorLeave:
        return await self._repo.create(
            id_medecin=id_medecin, date_absence=date_absence,
            motif=motif, journee_complete=journee_complete,
            heure_debut=heure_debut, heure_fin=heure_fin,
        )


class DeleteDoctorLeaveUseCase:
    def __init__(self, repo: AbstractDoctorLeaveRepository) -> None:
        self._repo = repo

    async def execute(self, leave_id: int) -> None:
        supprime = await self._repo.delete(leave_id)
        if not supprime:
            raise DoctorLeaveNotFoundError(leave_id)


# ── Note médecin ──────────────────────────────────────────────────────────────

class ListApprovedRatingsUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(
        self, id_medecin: int, params: PaginationParams
    ) -> Page[DoctorRating]:
        data, total = await self._repo.list_approved_by_doctor(id_medecin, params)
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
        id_medecin: int,
        id_utilisateur: int,
        note: int,
        commentaire: Optional[str] = None,
        id_rendez_vous: Optional[int] = None,
    ) -> DoctorRating:
        if await self._repo.user_already_rated(id_medecin, id_utilisateur):
            raise DuplicateRatingError(id_medecin, id_utilisateur)
        return await self._repo.create(
            id_medecin=id_medecin, id_utilisateur=id_utilisateur,
            note=note, commentaire=commentaire, id_rendez_vous=id_rendez_vous,
        )


class ApproveRatingUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(self, rating_id: int) -> DoctorRating:
        note = await self._repo.approve(rating_id)
        if note is None:
            raise DoctorRatingNotFoundError(rating_id)
        return note


class DeleteRatingUseCase:
    def __init__(self, repo: AbstractDoctorRatingRepository) -> None:
        self._repo = repo

    async def execute(self, rating_id: int) -> None:
        supprime = await self._repo.soft_delete(rating_id)
        if not supprime:
            raise DoctorRatingNotFoundError(rating_id)


# ── Réceptionniste ────────────────────────────────────────────────────────────

class CreateReceptionistUseCase:
    def __init__(self, repo: AbstractReceptionistRepository) -> None:
        self._repo = repo

    async def execute(self, id_utilisateur: int, id_clinique: int) -> Receptionist:
        return await self._repo.create(id_utilisateur=id_utilisateur, id_clinique=id_clinique)


class DeleteReceptionistUseCase:
    def __init__(self, repo: AbstractReceptionistRepository) -> None:
        self._repo = repo

    async def execute(self, receptionist_id: int) -> None:
        supprime = await self._repo.soft_delete(receptionist_id)
        if not supprime:
            raise ReceptionistNotFoundError(receptionist_id)
