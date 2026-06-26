"""Implémentations SQLAlchemy async des dépôts — module consultations médicales."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.consultation.domain.entites import (
    BodyChart,
    EncounterStatus,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.modules.consultation.domain.depots import (
    BodyChartRepository,
    EncounterRepository,
    MedicalReportRepository,
    PrescriptionRepository,
)
from app.modules.consultation.infrastructure.modeles import (
    AppointmentBodyChartModel,
    EncounterMedicalReportModel,
    EncounterPrescriptionModel,
    PatientEncounterModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Convertisseurs modèle → entité
# ---------------------------------------------------------------------------

def _enc_to_entity(m: PatientEncounterModel) -> PatientEncounter:
    return PatientEncounter(
        id=m.id,
        id_medecin=m.id_medecin,
        id_patient=m.id_patient,
        id_rendez_vous=m.id_rendez_vous,
        motif_principal=m.motif_principal,
        date_consultation=m.date_consultation,
        date_suivi=m.date_suivi,
        notes_suivi=m.notes_suivi,
        statut=EncounterStatus(m.statut),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _report_to_entity(m: EncounterMedicalReportModel) -> MedicalReport:
    return MedicalReport(
        id=m.id,
        id_consultation=m.id_consultation,
        symptomes=m.symptomes,
        diagnostic=m.diagnostic,
        traitement=m.traitement,
        tension_arterielle=m.tension_arterielle,
        temperature=m.temperature,
        poids=m.poids,
        notes_complementaires=m.notes_complementaires,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _presc_to_entity(m: EncounterPrescriptionModel) -> Prescription:
    return Prescription(
        id=m.id,
        id_consultation=m.id_consultation,
        nom_medicament=m.nom_medicament,
        posologie=m.posologie,
        frequence=m.frequence,
        duree_jours=m.duree_jours,
        instructions=m.instructions,
        est_chronique=m.est_chronique,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _chart_to_entity(m: AppointmentBodyChartModel) -> BodyChart:
    annotations = m.annotations
    if isinstance(annotations, dict):
        # Si stocké comme dict avec une clé "items", extraire la liste
        annotations = annotations.get("items", [])
    return BodyChart(
        id=m.id,
        id_rendez_vous=m.id_rendez_vous,
        url_image=m.url_image,
        annotations=annotations,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------

class SQLAlchemyEncounterRepository(EncounterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        id_medecin: int,
        id_patient: int,
        id_rendez_vous: Optional[int],
        motif_principal: Optional[str],
    ) -> PatientEncounter:
        consultation = PatientEncounterModel(
            id_medecin=id_medecin,
            id_patient=id_patient,
            id_rendez_vous=id_rendez_vous,
            motif_principal=motif_principal,
            date_consultation=datetime.utcnow(),
            statut="open",
        )
        self._session.add(consultation)
        await self._session.flush()
        await self._session.refresh(consultation)
        return _enc_to_entity(consultation)

    async def get_by_id(self, id_consultation: int) -> Optional[PatientEncounter]:
        requete = select(PatientEncounterModel).where(
            PatientEncounterModel.id == id_consultation,
            PatientEncounterModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _enc_to_entity(ligne) if ligne else None

    async def update(
        self,
        id_consultation: int,
        date_suivi: Optional[object],
        notes_suivi: Optional[str],
        statut: Optional[str],
    ) -> Optional[PatientEncounter]:
        requete = select(PatientEncounterModel).where(
            PatientEncounterModel.id == id_consultation,
            PatientEncounterModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        if date_suivi is not None:
            ligne.date_suivi = date_suivi
        if notes_suivi is not None:
            ligne.notes_suivi = notes_suivi
        if statut is not None:
            ligne.statut = statut
        await self._session.flush()
        await self._session.refresh(ligne)
        return _enc_to_entity(ligne)

    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[PatientEncounter], int]:
        requete_base = select(PatientEncounterModel).where(
            PatientEncounterModel.id_patient == id_patient,
            PatientEncounterModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(requete_base.subquery()))
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(PatientEncounterModel.date_consultation.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_enc_to_entity(r) for r in lignes], total

    async def list_all(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
        id_medecin: Optional[int] = None,
    ) -> tuple[list[PatientEncounter], int]:
        requete_base = select(PatientEncounterModel).where(
            PatientEncounterModel.deleted_at.is_(None)
        )
        if id_patient is not None:
            requete_base = requete_base.where(PatientEncounterModel.id_patient == id_patient)
        if id_medecin is not None:
            requete_base = requete_base.where(PatientEncounterModel.id_medecin == id_medecin)

        total: int = (
            await self._session.execute(select(func.count()).select_from(requete_base.subquery()))
        ).scalar_one()
        lignes = (
            await self._session.execute(
                requete_base.order_by(PatientEncounterModel.date_consultation.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_enc_to_entity(r) for r in lignes], total


class SQLAlchemyMedicalReportRepository(MedicalReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_encounter(self, id_consultation: int) -> Optional[MedicalReport]:
        requete = select(EncounterMedicalReportModel).where(
            EncounterMedicalReportModel.id_consultation == id_consultation
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _report_to_entity(ligne) if ligne else None

    async def upsert(
        self,
        id_consultation: int,
        symptomes: Optional[str],
        diagnostic: Optional[str],
        traitement: Optional[str],
        tension_arterielle: Optional[str],
        temperature: Optional[str],
        poids: Optional[str],
        notes_complementaires: Optional[str],
    ) -> MedicalReport:
        requete = select(EncounterMedicalReportModel).where(
            EncounterMedicalReportModel.id_consultation == id_consultation
        )
        rapport = (await self._session.execute(requete)).scalar_one_or_none()

        if rapport is None:
            rapport = EncounterMedicalReportModel(
                id_consultation=id_consultation,
                symptomes=symptomes,
                diagnostic=diagnostic,
                traitement=traitement,
                tension_arterielle=tension_arterielle,
                temperature=temperature,
                poids=poids,
                notes_complementaires=notes_complementaires,
            )
            self._session.add(rapport)
        else:
            if symptomes is not None:
                rapport.symptomes = symptomes
            if diagnostic is not None:
                rapport.diagnostic = diagnostic
            if traitement is not None:
                rapport.traitement = traitement
            if tension_arterielle is not None:
                rapport.tension_arterielle = tension_arterielle
            if temperature is not None:
                rapport.temperature = temperature
            if poids is not None:
                rapport.poids = poids
            if notes_complementaires is not None:
                rapport.notes_complementaires = notes_complementaires
            rapport.updated_at = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(rapport)
        return _report_to_entity(rapport)


class SQLAlchemyPrescriptionRepository(PrescriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_encounter(self, id_consultation: int) -> list[Prescription]:
        requete = select(EncounterPrescriptionModel).where(
            EncounterPrescriptionModel.id_consultation == id_consultation,
            EncounterPrescriptionModel.deleted_at.is_(None),
        )
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_presc_to_entity(r) for r in lignes]

    async def list_active_by_patient(self, id_patient: int) -> list[Prescription]:
        """Récupère toutes les ordonnances actives d'un patient via ses consultations."""
        requete = (
            select(EncounterPrescriptionModel)
            .join(
                PatientEncounterModel,
                EncounterPrescriptionModel.id_consultation == PatientEncounterModel.id,
            )
            .where(
                PatientEncounterModel.id_patient == id_patient,
                PatientEncounterModel.deleted_at.is_(None),
                EncounterPrescriptionModel.deleted_at.is_(None),
            )
            .order_by(EncounterPrescriptionModel.created_at.desc())
        )
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_presc_to_entity(r) for r in lignes]

    async def create(
        self,
        id_consultation: int,
        nom_medicament: str,
        posologie: Optional[str],
        frequence: Optional[str],
        duree_jours: Optional[int],
        instructions: Optional[str],
        est_chronique: bool,
    ) -> Prescription:
        ordonnance = EncounterPrescriptionModel(
            id_consultation=id_consultation,
            nom_medicament=nom_medicament,
            posologie=posologie,
            frequence=frequence,
            duree_jours=duree_jours,
            instructions=instructions,
            est_chronique=est_chronique,
        )
        self._session.add(ordonnance)
        await self._session.flush()
        await self._session.refresh(ordonnance)
        return _presc_to_entity(ordonnance)

    async def soft_delete(self, prescription_id: int) -> bool:
        requete = select(EncounterPrescriptionModel).where(
            EncounterPrescriptionModel.id == prescription_id,
            EncounterPrescriptionModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyBodyChartRepository(BodyChartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_appointment(self, id_rendez_vous: int) -> Optional[BodyChart]:
        requete = select(AppointmentBodyChartModel).where(
            AppointmentBodyChartModel.id_rendez_vous == id_rendez_vous,
            AppointmentBodyChartModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _chart_to_entity(ligne) if ligne else None

    async def upsert(
        self,
        id_rendez_vous: int,
        url_image: str,
        annotations: Optional[list],
        notes: Optional[str],
    ) -> BodyChart:
        requete = select(AppointmentBodyChartModel).where(
            AppointmentBodyChartModel.id_rendez_vous == id_rendez_vous,
            AppointmentBodyChartModel.deleted_at.is_(None),
        )
        schema_anatomique = (await self._session.execute(requete)).scalar_one_or_none()

        if schema_anatomique is None:
            schema_anatomique = AppointmentBodyChartModel(
                id_rendez_vous=id_rendez_vous,
                url_image=url_image,
                annotations=annotations,
                notes=notes,
            )
            self._session.add(schema_anatomique)
        else:
            schema_anatomique.url_image = url_image
            if annotations is not None:
                schema_anatomique.annotations = annotations
            if notes is not None:
                schema_anatomique.notes = notes

        await self._session.flush()
        await self._session.refresh(schema_anatomique)
        return _chart_to_entity(schema_anatomique)
