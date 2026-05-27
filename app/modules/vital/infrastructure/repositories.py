"""SQLAlchemy repositories — module vital."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.vital.domain.entities import VitalSigns, VitalStats
from app.modules.vital.domain.repositories import AbstractVitalSignsRepository
from app.modules.vital.infrastructure.models import VitalSignsModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: VitalSignsModel) -> VitalSigns:
    return VitalSigns(
        id=m.id,
        patient_id=m.patient_id,
        recorded_by=m.recorded_by,
        appointment_id=m.appointment_id,
        blood_pressure_systolic=m.blood_pressure_systolic,
        blood_pressure_diastolic=m.blood_pressure_diastolic,
        heart_rate=m.heart_rate,
        temperature=m.temperature,
        weight=m.weight,
        height=m.height,
        oxygen_saturation=m.oxygen_saturation,
        blood_sugar=m.blood_sugar,
        notes=m.notes,
        recorded_at=m.recorded_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


class SQLVitalSignsRepository(AbstractVitalSignsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[VitalSigns], int]:
        base = select(VitalSignsModel).where(
            VitalSignsModel.patient_id == patient_id,
            VitalSignsModel.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(VitalSignsModel.recorded_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_entity(m) for m in result.scalars().all()], total

    async def list_all_paginated(
        self,
        params: PaginationParams,
        patient_id: Optional[int] = None,
    ) -> tuple[list[VitalSigns], int]:
        base = select(VitalSignsModel).where(VitalSignsModel.deleted_at.is_(None))
        if patient_id is not None:
            base = base.where(VitalSignsModel.patient_id == patient_id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(VitalSignsModel.recorded_at.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_entity(m) for m in result.scalars().all()], total

    async def get_by_id(self, vital_id: int) -> Optional[VitalSigns]:
        stmt = select(VitalSignsModel).where(VitalSignsModel.id == vital_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self,
        patient_id: int,
        recorded_by: Optional[int] = None,
        appointment_id: Optional[int] = None,
        blood_pressure_systolic: Optional[int] = None,
        blood_pressure_diastolic: Optional[int] = None,
        heart_rate: Optional[int] = None,
        temperature: Optional[Decimal] = None,
        weight: Optional[Decimal] = None,
        height: Optional[Decimal] = None,
        oxygen_saturation: Optional[int] = None,
        blood_sugar: Optional[Decimal] = None,
        notes: Optional[str] = None,
        recorded_at: Optional[datetime] = None,
    ) -> VitalSigns:
        kwargs = dict(
            patient_id=patient_id,
            recorded_by=recorded_by,
            appointment_id=appointment_id,
            blood_pressure_systolic=blood_pressure_systolic,
            blood_pressure_diastolic=blood_pressure_diastolic,
            heart_rate=heart_rate,
            temperature=temperature,
            weight=weight,
            height=height,
            oxygen_saturation=oxygen_saturation,
            blood_sugar=blood_sugar,
            notes=notes,
        )
        if recorded_at is not None:
            kwargs["recorded_at"] = recorded_at
        m = VitalSignsModel(**kwargs)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(self, vital_id: int, **kwargs) -> Optional[VitalSigns]:
        stmt = (
            update(VitalSignsModel)
            .where(VitalSignsModel.id == vital_id, VitalSignsModel.deleted_at.is_(None))
            .values(**kwargs)
            .returning(VitalSignsModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def soft_delete(self, vital_id: int) -> bool:
        stmt = (
            update(VitalSignsModel)
            .where(VitalSignsModel.id == vital_id, VitalSignsModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_stats(self, patient_id: int) -> VitalStats:
        """Récupère la dernière valeur de chaque type de constante."""
        stmt = (
            select(VitalSignsModel)
            .where(
                VitalSignsModel.patient_id == patient_id,
                VitalSignsModel.deleted_at.is_(None),
            )
            .order_by(VitalSignsModel.recorded_at.desc())
            .limit(50)  # suffisant pour extraire les dernières valeurs de chaque type
        )
        result = await self._session.execute(stmt)
        records = result.scalars().all()

        stats = VitalStats(patient_id=patient_id)
        for m in records:
            if stats.last_blood_pressure_systolic is None and m.blood_pressure_systolic is not None:
                stats.last_blood_pressure_systolic = m.blood_pressure_systolic
            if stats.last_blood_pressure_diastolic is None and m.blood_pressure_diastolic is not None:
                stats.last_blood_pressure_diastolic = m.blood_pressure_diastolic
            if stats.last_heart_rate is None and m.heart_rate is not None:
                stats.last_heart_rate = m.heart_rate
            if stats.last_temperature is None and m.temperature is not None:
                stats.last_temperature = m.temperature
            if stats.last_weight is None and m.weight is not None:
                stats.last_weight = m.weight
            if stats.last_height is None and m.height is not None:
                stats.last_height = m.height
            if stats.last_oxygen_saturation is None and m.oxygen_saturation is not None:
                stats.last_oxygen_saturation = m.oxygen_saturation
            if stats.last_blood_sugar is None and m.blood_sugar is not None:
                stats.last_blood_sugar = m.blood_sugar

        # Calcul BMI à partir des dernières valeurs
        if stats.last_weight is not None and stats.last_height is not None and stats.last_height > 0:
            h_m = float(stats.last_height) / 100.0
            stats.last_bmi = round(float(stats.last_weight) / (h_m ** 2), 2)

        return stats
