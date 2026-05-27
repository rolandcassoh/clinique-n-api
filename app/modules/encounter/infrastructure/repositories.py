"""Implémentations SQLAlchemy async des repositories encounter."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.encounter.domain.entities import (
    BodyChart,
    EncounterStatus,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.modules.encounter.domain.repositories import (
    BodyChartRepository,
    EncounterRepository,
    MedicalReportRepository,
    PrescriptionRepository,
)
from app.modules.encounter.infrastructure.models import (
    AppointmentBodyChartModel,
    EncounterMedicalReportModel,
    EncounterPrescriptionModel,
    PatientEncounterModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------

def _enc_to_entity(m: PatientEncounterModel) -> PatientEncounter:
    return PatientEncounter(
        id=m.id,
        doctor_id=m.doctor_id,
        patient_id=m.patient_id,
        appointment_id=m.appointment_id,
        chief_complaint=m.chief_complaint,
        encounter_date=m.encounter_date,
        follow_up_date=m.follow_up_date,
        follow_up_notes=m.follow_up_notes,
        status=EncounterStatus(m.status),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _report_to_entity(m: EncounterMedicalReportModel) -> MedicalReport:
    return MedicalReport(
        id=m.id,
        encounter_id=m.encounter_id,
        symptoms=m.symptoms,
        diagnosis=m.diagnosis,
        treatment=m.treatment,
        blood_pressure=m.blood_pressure,
        temperature=m.temperature,
        weight=m.weight,
        additional_notes=m.additional_notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _presc_to_entity(m: EncounterPrescriptionModel) -> Prescription:
    return Prescription(
        id=m.id,
        encounter_id=m.encounter_id,
        medication_name=m.medication_name,
        dosage=m.dosage,
        frequency=m.frequency,
        duration_days=m.duration_days,
        instructions=m.instructions,
        is_chronic=m.is_chronic,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _chart_to_entity(m: AppointmentBodyChartModel) -> BodyChart:
    ann = m.annotations
    if isinstance(ann, dict):
        # Si stocké comme dict avec une clé "items", extraire la liste
        ann = ann.get("items", [])
    return BodyChart(
        id=m.id,
        appointment_id=m.appointment_id,
        image_url=m.image_url,
        annotations=ann,
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
        doctor_id: int,
        patient_id: int,
        appointment_id: Optional[int],
        chief_complaint: Optional[str],
    ) -> PatientEncounter:
        enc = PatientEncounterModel(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            chief_complaint=chief_complaint,
            encounter_date=datetime.utcnow(),
            status="open",
        )
        self._session.add(enc)
        await self._session.flush()
        await self._session.refresh(enc)
        return _enc_to_entity(enc)

    async def get_by_id(self, encounter_id: int) -> Optional[PatientEncounter]:
        q = select(PatientEncounterModel).where(
            PatientEncounterModel.id == encounter_id,
            PatientEncounterModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _enc_to_entity(row) if row else None

    async def update(
        self,
        encounter_id: int,
        follow_up_date: Optional[object],
        follow_up_notes: Optional[str],
        status: Optional[str],
    ) -> Optional[PatientEncounter]:
        q = select(PatientEncounterModel).where(
            PatientEncounterModel.id == encounter_id,
            PatientEncounterModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if follow_up_date is not None:
            row.follow_up_date = follow_up_date
        if follow_up_notes is not None:
            row.follow_up_notes = follow_up_notes
        if status is not None:
            row.status = status
        await self._session.flush()
        await self._session.refresh(row)
        return _enc_to_entity(row)

    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[PatientEncounter], int]:
        base = select(PatientEncounterModel).where(
            PatientEncounterModel.patient_id == patient_id,
            PatientEncounterModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(PatientEncounterModel.encounter_date.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_enc_to_entity(r) for r in rows], total

    async def list_all(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
    ) -> tuple[list[PatientEncounter], int]:
        base = select(PatientEncounterModel).where(
            PatientEncounterModel.deleted_at.is_(None)
        )
        if patient_id is not None:
            base = base.where(PatientEncounterModel.patient_id == patient_id)
        if doctor_id is not None:
            base = base.where(PatientEncounterModel.doctor_id == doctor_id)

        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(PatientEncounterModel.encounter_date.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_enc_to_entity(r) for r in rows], total


class SQLAlchemyMedicalReportRepository(MedicalReportRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_encounter(self, encounter_id: int) -> Optional[MedicalReport]:
        q = select(EncounterMedicalReportModel).where(
            EncounterMedicalReportModel.encounter_id == encounter_id
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _report_to_entity(row) if row else None

    async def upsert(
        self,
        encounter_id: int,
        symptoms: Optional[str],
        diagnosis: Optional[str],
        treatment: Optional[str],
        blood_pressure: Optional[str],
        temperature: Optional[str],
        weight: Optional[str],
        additional_notes: Optional[str],
    ) -> MedicalReport:
        q = select(EncounterMedicalReportModel).where(
            EncounterMedicalReportModel.encounter_id == encounter_id
        )
        row = (await self._session.execute(q)).scalar_one_or_none()

        if row is None:
            row = EncounterMedicalReportModel(
                encounter_id=encounter_id,
                symptoms=symptoms,
                diagnosis=diagnosis,
                treatment=treatment,
                blood_pressure=blood_pressure,
                temperature=temperature,
                weight=weight,
                additional_notes=additional_notes,
            )
            self._session.add(row)
        else:
            if symptoms is not None:
                row.symptoms = symptoms
            if diagnosis is not None:
                row.diagnosis = diagnosis
            if treatment is not None:
                row.treatment = treatment
            if blood_pressure is not None:
                row.blood_pressure = blood_pressure
            if temperature is not None:
                row.temperature = temperature
            if weight is not None:
                row.weight = weight
            if additional_notes is not None:
                row.additional_notes = additional_notes
            row.updated_at = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(row)
        return _report_to_entity(row)


class SQLAlchemyPrescriptionRepository(PrescriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_encounter(self, encounter_id: int) -> list[Prescription]:
        q = select(EncounterPrescriptionModel).where(
            EncounterPrescriptionModel.encounter_id == encounter_id,
            EncounterPrescriptionModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_presc_to_entity(r) for r in rows]

    async def list_active_by_patient(self, patient_id: int) -> list[Prescription]:
        """Récupère toutes les ordonnances actives d'un patient via ses consultations."""
        q = (
            select(EncounterPrescriptionModel)
            .join(
                PatientEncounterModel,
                EncounterPrescriptionModel.encounter_id == PatientEncounterModel.id,
            )
            .where(
                PatientEncounterModel.patient_id == patient_id,
                PatientEncounterModel.deleted_at.is_(None),
                EncounterPrescriptionModel.deleted_at.is_(None),
            )
            .order_by(EncounterPrescriptionModel.created_at.desc())
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_presc_to_entity(r) for r in rows]

    async def create(
        self,
        encounter_id: int,
        medication_name: str,
        dosage: Optional[str],
        frequency: Optional[str],
        duration_days: Optional[int],
        instructions: Optional[str],
        is_chronic: bool,
    ) -> Prescription:
        presc = EncounterPrescriptionModel(
            encounter_id=encounter_id,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            instructions=instructions,
            is_chronic=is_chronic,
        )
        self._session.add(presc)
        await self._session.flush()
        await self._session.refresh(presc)
        return _presc_to_entity(presc)

    async def soft_delete(self, prescription_id: int) -> bool:
        q = select(EncounterPrescriptionModel).where(
            EncounterPrescriptionModel.id == prescription_id,
            EncounterPrescriptionModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyBodyChartRepository(BodyChartRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_appointment(self, appointment_id: int) -> Optional[BodyChart]:
        q = select(AppointmentBodyChartModel).where(
            AppointmentBodyChartModel.appointment_id == appointment_id,
            AppointmentBodyChartModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _chart_to_entity(row) if row else None

    async def upsert(
        self,
        appointment_id: int,
        image_url: str,
        annotations: Optional[list],
        notes: Optional[str],
    ) -> BodyChart:
        q = select(AppointmentBodyChartModel).where(
            AppointmentBodyChartModel.appointment_id == appointment_id,
            AppointmentBodyChartModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()

        if row is None:
            row = AppointmentBodyChartModel(
                appointment_id=appointment_id,
                image_url=image_url,
                annotations=annotations,
                notes=notes,
            )
            self._session.add(row)
        else:
            row.image_url = image_url
            if annotations is not None:
                row.annotations = annotations
            if notes is not None:
                row.notes = notes

        await self._session.flush()
        await self._session.refresh(row)
        return _chart_to_entity(row)
