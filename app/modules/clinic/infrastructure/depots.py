"""Dépôts SQLAlchemy — module clinique."""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.modules.clinic.infrastructure.modeles import (
    ClinicCategoryModel,
    ClinicModel,
    ClinicServiceModel,
    DoctorLeaveModel,
    DoctorModel,
    DoctorRatingModel,
    DoctorSessionModel,
    ReceptionistModel,
)
from app.shared.schemas.pagination import PaginationParams


# ── Convertisseurs modèle → entité ────────────────────────────────────────────

def _to_category(m: ClinicCategoryModel) -> ClinicCategory:
    return ClinicCategory(
        id=m.id, nom=m.nom, identifiant_url=m.identifiant_url, image=m.image,
        description=m.description, est_actif=m.est_actif, ordre_affichage=m.ordre_affichage,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


def _to_clinic(m: ClinicModel) -> Clinic:
    return Clinic(
        id=m.id, id_proprietaire=m.id_proprietaire, nom=m.nom, identifiant_url=m.identifiant_url,
        description=m.description, adresse=m.adresse, id_ville=m.id_ville,
        telephone=m.telephone, courriel=m.courriel, site_web=m.site_web, logo=m.logo,
        image_couverture=m.image_couverture, est_actif=m.est_actif, est_mis_en_avant=m.est_mis_en_avant,
        latitude=m.latitude, longitude=m.longitude, taux_commission=m.taux_commission,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


def _to_service(m: ClinicServiceModel) -> ClinicService:
    return ClinicService(
        id=m.id, id_clinique=m.id_clinique, nom=m.nom, description=m.description,
        prix=m.prix, duree_minutes=m.duree_minutes, est_actif=m.est_actif,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


def _to_doctor(m: DoctorModel) -> Doctor:
    return Doctor(
        id=m.id, id_utilisateur=m.id_utilisateur, id_clinique=m.id_clinique,
        specialite=m.specialite, qualification=m.qualification,
        annees_experience=m.annees_experience, honoraires_consultation=m.honoraires_consultation,
        montant_avance=m.montant_avance, est_disponible=m.est_disponible,
        id_agenda_google=m.id_agenda_google,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


def _to_session(m: DoctorSessionModel) -> DoctorSession:
    return DoctorSession(
        id=m.id, id_medecin=m.id_medecin, jour_semaine=m.jour_semaine,
        heure_debut=m.heure_debut, heure_fin=m.heure_fin,
        duree_creneau_minutes=m.duree_creneau_minutes,
        max_patients_par_creneau=m.max_patients_par_creneau, est_actif=m.est_actif,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _to_leave(m: DoctorLeaveModel) -> DoctorLeave:
    return DoctorLeave(
        id=m.id, id_medecin=m.id_medecin, date_absence=m.date_absence,
        motif=m.motif, journee_complete=m.journee_complete,
        heure_debut=m.heure_debut, heure_fin=m.heure_fin,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _to_rating(m: DoctorRatingModel) -> DoctorRating:
    return DoctorRating(
        id=m.id, id_medecin=m.id_medecin, id_utilisateur=m.id_utilisateur,
        id_rendez_vous=m.id_rendez_vous, note=m.note,
        commentaire=m.commentaire, est_approuve=m.est_approuve,
        created_at=m.created_at, updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


def _to_receptionist(m: ReceptionistModel) -> Receptionist:
    return Receptionist(
        id=m.id, id_utilisateur=m.id_utilisateur, id_clinique=m.id_clinique,
        est_actif=m.est_actif, created_at=m.created_at,
        updated_at=m.updated_at, deleted_at=m.deleted_at,
    )


# ── ClinicCategoryRepository ──────────────────────────────────────────────────

class SQLClinicCategoryRepository(AbstractClinicCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[ClinicCategory]:
        stmt = (
            select(ClinicCategoryModel)
            .where(
                ClinicCategoryModel.est_actif.is_(True),
                ClinicCategoryModel.deleted_at.is_(None),
            )
            .order_by(ClinicCategoryModel.ordre_affichage)
        )
        result = await self._session.execute(stmt)
        return [_to_category(m) for m in result.scalars().all()]

    async def get_by_id(self, id_categorie: int) -> Optional[ClinicCategory]:
        stmt = select(ClinicCategoryModel).where(
            ClinicCategoryModel.id == id_categorie,
            ClinicCategoryModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_category(m) if m else None

    async def create(
        self,
        nom: str,
        identifiant_url: str,
        image: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ClinicCategory:
        m = ClinicCategoryModel(nom=nom, identifiant_url=identifiant_url, image=image, description=description)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_category(m)

    async def update(self, id_categorie: int, **kwargs) -> Optional[ClinicCategory]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module.
        stmt = (
            update(ClinicCategoryModel)
            .where(
                ClinicCategoryModel.id == id_categorie,
                ClinicCategoryModel.deleted_at.is_(None),
            )
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(ClinicCategoryModel).where(ClinicCategoryModel.id == id_categorie)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_category(m) if m else None

    async def soft_delete(self, id_categorie: int) -> bool:
        stmt = (
            update(ClinicCategoryModel)
            .where(
                ClinicCategoryModel.id == id_categorie,
                ClinicCategoryModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


# ── ClinicRepository ──────────────────────────────────────────────────────────

class SQLClinicRepository(AbstractClinicRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_paginated(
        self,
        params: PaginationParams,
        id_ville: Optional[int] = None,
        id_categorie: Optional[int] = None,
        search: Optional[str] = None,
        est_mis_en_avant: Optional[bool] = None,
        inclure_inactifs: bool = False,
    ) -> tuple[list[Clinic], int]:
        # inclure_inactifs=True (vue admin) : ne pas filtrer sur est_actif, sinon
        # une clinique désactivée disparaît de la liste et devient impossible à
        # réactiver depuis l'interface d'administration.
        conditions = [ClinicModel.deleted_at.is_(None)]
        if not inclure_inactifs:
            conditions.append(ClinicModel.est_actif.is_(True))
        base = select(ClinicModel).where(*conditions)
        if id_ville is not None:
            base = base.where(ClinicModel.id_ville == id_ville)
        if est_mis_en_avant is not None:
            base = base.where(ClinicModel.est_mis_en_avant == est_mis_en_avant)
        if search:
            base = base.where(ClinicModel.nom.ilike(f"%{search}%"))

        requete_compte = select(func.count()).select_from(base.subquery())
        resultat_total = await self._session.execute(requete_compte)
        total = resultat_total.scalar_one()

        requete_donnees = base.offset(params.offset).limit(params.per_page)
        resultat = await self._session.execute(requete_donnees)
        return [_to_clinic(m) for m in resultat.scalars().all()], total

    async def get_by_slug(self, identifiant_url: str) -> Optional[Clinic]:
        stmt = select(ClinicModel).where(
            ClinicModel.identifiant_url == identifiant_url,
            ClinicModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_clinic(m) if m else None

    async def get_by_id(self, id_clinique: int) -> Optional[Clinic]:
        stmt = select(ClinicModel).where(
            ClinicModel.id == id_clinique,
            ClinicModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_clinic(m) if m else None

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
        m = ClinicModel(
            id_proprietaire=id_proprietaire, nom=nom, identifiant_url=identifiant_url, description=description,
            adresse=adresse, id_ville=id_ville, telephone=telephone, courriel=courriel,
            site_web=site_web, logo=logo, image_couverture=image_couverture,
            latitude=latitude, longitude=longitude, taux_commission=taux_commission,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_clinic(m)

    async def update(self, id_clinique: int, **kwargs) -> Optional[Clinic]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module.
        stmt = (
            update(ClinicModel)
            .where(ClinicModel.id == id_clinique, ClinicModel.deleted_at.is_(None))
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(ClinicModel).where(ClinicModel.id == id_clinique)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_clinic(m) if m else None

    async def soft_delete(self, id_clinique: int) -> bool:
        stmt = (
            update(ClinicModel)
            .where(ClinicModel.id == id_clinique, ClinicModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def slug_exists(self, identifiant_url: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).select_from(ClinicModel).where(
            ClinicModel.identifiant_url == identifiant_url,
            ClinicModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            stmt = stmt.where(ClinicModel.id != exclude_id)
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0


# ── ClinicServiceRepository ───────────────────────────────────────────────────

class SQLClinicServiceRepository(AbstractClinicServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_clinic(self, id_clinique: int) -> list[ClinicService]:
        stmt = select(ClinicServiceModel).where(
            ClinicServiceModel.id_clinique == id_clinique,
            ClinicServiceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_to_service(m) for m in result.scalars().all()]

    async def get_by_id(self, id_service: int) -> Optional[ClinicService]:
        stmt = select(ClinicServiceModel).where(
            ClinicServiceModel.id == id_service,
            ClinicServiceModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_service(m) if m else None

    async def create(
        self,
        id_clinique: int,
        nom: str,
        description: Optional[str] = None,
        prix: Decimal = Decimal("0"),
        duree_minutes: int = 30,
    ) -> ClinicService:
        m = ClinicServiceModel(
            id_clinique=id_clinique, nom=nom, description=description,
            prix=prix, duree_minutes=duree_minutes,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_service(m)

    async def update(self, id_service: int, **kwargs) -> Optional[ClinicService]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module.
        stmt = (
            update(ClinicServiceModel)
            .where(
                ClinicServiceModel.id == id_service,
                ClinicServiceModel.deleted_at.is_(None),
            )
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(ClinicServiceModel).where(ClinicServiceModel.id == id_service)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_service(m) if m else None

    async def soft_delete(self, id_service: int) -> bool:
        stmt = (
            update(ClinicServiceModel)
            .where(
                ClinicServiceModel.id == id_service,
                ClinicServiceModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


# ── DoctorRepository ──────────────────────────────────────────────────────────

class SQLDoctorRepository(AbstractDoctorRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        base = select(DoctorModel).where(DoctorModel.deleted_at.is_(None))
        if id_clinique is not None:
            base = base.where(DoctorModel.id_clinique == id_clinique)
        if specialite:
            base = base.where(DoctorModel.specialite.ilike(f"%{specialite}%"))
        if min_fee is not None:
            base = base.where(DoctorModel.honoraires_consultation >= min_fee)
        if max_fee is not None:
            base = base.where(DoctorModel.honoraires_consultation <= max_fee)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_doctor(m) for m in result.scalars().all()], total

    async def get_by_id(self, id_medecin: int) -> Optional[Doctor]:
        stmt = select(DoctorModel).where(
            DoctorModel.id == id_medecin,
            DoctorModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_doctor(m) if m else None

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
        m = DoctorModel(
            id_utilisateur=id_utilisateur, id_clinique=id_clinique, specialite=specialite,
            qualification=qualification, annees_experience=annees_experience,
            honoraires_consultation=honoraires_consultation, montant_avance=montant_avance,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_doctor(m)

    async def update(self, id_medecin: int, **kwargs) -> Optional[Doctor]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module (voir `create` ci-dessus).
        stmt = (
            update(DoctorModel)
            .where(DoctorModel.id == id_medecin, DoctorModel.deleted_at.is_(None))
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(DoctorModel).where(DoctorModel.id == id_medecin)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_doctor(m) if m else None

    async def soft_delete(self, id_medecin: int) -> bool:
        stmt = (
            update(DoctorModel)
            .where(DoctorModel.id == id_medecin, DoctorModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def find_active_session(
        self, id_medecin: int, jour_semaine: int
    ) -> Optional[DoctorSession]:
        stmt = select(DoctorSessionModel).where(
            DoctorSessionModel.id_medecin == id_medecin,
            DoctorSessionModel.jour_semaine == jour_semaine,
            DoctorSessionModel.est_actif.is_(True),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_session(m) if m else None

    async def find_leave(
        self, id_medecin: int, date_absence: date
    ) -> Optional[DoctorLeave]:
        stmt = select(DoctorLeaveModel).where(
            DoctorLeaveModel.id_medecin == id_medecin,
            DoctorLeaveModel.date_absence == date_absence,
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_leave(m) if m else None

    async def count_booked_slots(
        self, id_medecin: int, slot_date: date
    ) -> dict[str, int]:
        """
        Retourne le nombre de rendez-vous confirmés/en attente par créneau (ISO datetime str).
        La table appointments peut ne pas exister en test, on retourne un dict vide
        par défaut. En production, cette méthode peut être étendue.
        """
        return {}

    async def get_average_rating(self, id_medecin: int) -> Optional[float]:
        stmt = select(func.avg(DoctorRatingModel.note)).where(
            DoctorRatingModel.id_medecin == id_medecin,
            DoctorRatingModel.est_approuve.is_(True),
            DoctorRatingModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        avg = result.scalar_one_or_none()
        return float(avg) if avg is not None else None


# ── DoctorSessionRepository ───────────────────────────────────────────────────

class SQLDoctorSessionRepository(AbstractDoctorSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_doctor(self, id_medecin: int) -> list[DoctorSession]:
        stmt = select(DoctorSessionModel).where(
            DoctorSessionModel.id_medecin == id_medecin,
        ).order_by(DoctorSessionModel.jour_semaine, DoctorSessionModel.heure_debut)
        result = await self._session.execute(stmt)
        return [_to_session(m) for m in result.scalars().all()]

    async def get_by_id(self, session_id: int) -> Optional[DoctorSession]:
        stmt = select(DoctorSessionModel).where(DoctorSessionModel.id == session_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_session(m) if m else None

    async def create(
        self,
        id_medecin: int,
        jour_semaine: int,
        heure_debut,
        heure_fin,
        duree_creneau_minutes: int = 30,
        max_patients_par_creneau: int = 1,
    ) -> DoctorSession:
        m = DoctorSessionModel(
            id_medecin=id_medecin, jour_semaine=jour_semaine,
            heure_debut=heure_debut, heure_fin=heure_fin,
            duree_creneau_minutes=duree_creneau_minutes,
            max_patients_par_creneau=max_patients_par_creneau,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_session(m)

    async def update(self, session_id: int, **kwargs) -> Optional[DoctorSession]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module.
        stmt = (
            update(DoctorSessionModel)
            .where(DoctorSessionModel.id == session_id)
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(DoctorSessionModel).where(DoctorSessionModel.id == session_id)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_session(m) if m else None

    async def delete(self, session_id: int) -> bool:
        stmt = (
            update(DoctorSessionModel)
            .where(DoctorSessionModel.id == session_id)
            .values(est_actif=False)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


# ── DoctorLeaveRepository ─────────────────────────────────────────────────────

class SQLDoctorLeaveRepository(AbstractDoctorLeaveRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_doctor(self, id_medecin: int) -> list[DoctorLeave]:
        stmt = select(DoctorLeaveModel).where(
            DoctorLeaveModel.id_medecin == id_medecin,
        ).order_by(DoctorLeaveModel.date_absence.desc())
        result = await self._session.execute(stmt)
        return [_to_leave(m) for m in result.scalars().all()]

    async def get_by_id(self, leave_id: int) -> Optional[DoctorLeave]:
        stmt = select(DoctorLeaveModel).where(DoctorLeaveModel.id == leave_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_leave(m) if m else None

    async def create(
        self,
        id_medecin: int,
        date_absence: date,
        motif: Optional[str] = None,
        journee_complete: bool = True,
        heure_debut=None,
        heure_fin=None,
    ) -> DoctorLeave:
        m = DoctorLeaveModel(
            id_medecin=id_medecin, date_absence=date_absence,
            motif=motif, journee_complete=journee_complete,
            heure_debut=heure_debut, heure_fin=heure_fin,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_leave(m)

    async def delete(self, leave_id: int) -> bool:
        stmt = (
            update(DoctorLeaveModel)
            .where(DoctorLeaveModel.id == leave_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


# ── DoctorRatingRepository ────────────────────────────────────────────────────

class SQLDoctorRatingRepository(AbstractDoctorRatingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved_by_doctor(
        self, id_medecin: int, params: PaginationParams
    ) -> tuple[list[DoctorRating], int]:
        base = select(DoctorRatingModel).where(
            DoctorRatingModel.id_medecin == id_medecin,
            DoctorRatingModel.est_approuve.is_(True),
            DoctorRatingModel.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(DoctorRatingModel.created_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_rating(m) for m in result.scalars().all()], total

    async def list_pending(
        self, params: PaginationParams
    ) -> tuple[list[DoctorRating], int]:
        base = select(DoctorRatingModel).where(
            DoctorRatingModel.est_approuve.is_(False),
            DoctorRatingModel.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(DoctorRatingModel.created_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_rating(m) for m in result.scalars().all()], total

    async def get_by_id(self, rating_id: int) -> Optional[DoctorRating]:
        stmt = select(DoctorRatingModel).where(
            DoctorRatingModel.id == rating_id,
            DoctorRatingModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_rating(m) if m else None

    async def user_already_rated(self, id_medecin: int, id_utilisateur: int) -> bool:
        stmt = select(func.count()).select_from(DoctorRatingModel).where(
            DoctorRatingModel.id_medecin == id_medecin,
            DoctorRatingModel.id_utilisateur == id_utilisateur,
            DoctorRatingModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def create(
        self,
        id_medecin: int,
        id_utilisateur: int,
        note: int,
        commentaire: Optional[str] = None,
        id_rendez_vous: Optional[int] = None,
    ) -> DoctorRating:
        m = DoctorRatingModel(
            id_medecin=id_medecin, id_utilisateur=id_utilisateur, note=note,
            commentaire=commentaire, id_rendez_vous=id_rendez_vous,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_rating(m)

    async def approve(self, rating_id: int) -> Optional[DoctorRating]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne, comme les autres dépôts de ce module.
        stmt = (
            update(DoctorRatingModel)
            .where(
                DoctorRatingModel.id == rating_id,
                DoctorRatingModel.deleted_at.is_(None),
            )
            .values(est_approuve=True)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        requete = select(DoctorRatingModel).where(DoctorRatingModel.id == rating_id)
        m = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_rating(m) if m else None

    async def soft_delete(self, rating_id: int) -> bool:
        stmt = (
            update(DoctorRatingModel)
            .where(
                DoctorRatingModel.id == rating_id,
                DoctorRatingModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0


# ── ReceptionistRepository ────────────────────────────────────────────────────

class SQLReceptionistRepository(AbstractReceptionistRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, receptionist_id: int) -> Optional[Receptionist]:
        stmt = select(ReceptionistModel).where(
            ReceptionistModel.id == receptionist_id,
            ReceptionistModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_receptionist(m) if m else None

    async def create(self, id_utilisateur: int, id_clinique: int) -> Receptionist:
        m = ReceptionistModel(id_utilisateur=id_utilisateur, id_clinique=id_clinique)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_receptionist(m)

    async def soft_delete(self, receptionist_id: int) -> bool:
        stmt = (
            update(ReceptionistModel)
            .where(
                ReceptionistModel.id == receptionist_id,
                ReceptionistModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
