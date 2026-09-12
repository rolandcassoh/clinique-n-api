"""Dépôts SQLAlchemy — module constantes vitales."""
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.signe_vital.domain.entites import VitalSigns, VitalStats
from app.modules.signe_vital.domain.depots import AbstractVitalSignsRepository
from app.modules.signe_vital.infrastructure.modeles import VitalSignsModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: VitalSignsModel) -> VitalSigns:
    return VitalSigns(
        id=m.id,
        id_patient=m.id_patient,
        enregistre_par=m.enregistre_par,
        id_rendez_vous=m.id_rendez_vous,
        tension_systolique=m.tension_systolique,
        tension_diastolique=m.tension_diastolique,
        frequence_cardiaque=m.frequence_cardiaque,
        temperature=m.temperature,
        poids=m.poids,
        taille=m.taille,
        saturation_oxygene=m.saturation_oxygene,
        glycemie=m.glycemie,
        notes=m.notes,
        enregistre_le=m.enregistre_le,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
    )


class SQLVitalSignsRepository(AbstractVitalSignsRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[VitalSigns], int]:
        base = select(VitalSignsModel).where(
            VitalSignsModel.id_patient == id_patient,
            VitalSignsModel.deleted_at.is_(None),
        )
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(VitalSignsModel.enregistre_le.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_entity(m) for m in result.scalars().all()], total

    async def list_all_paginated(
        self,
        params: PaginationParams,
        id_patient: Optional[int] = None,
    ) -> tuple[list[VitalSigns], int]:
        base = select(VitalSignsModel).where(VitalSignsModel.deleted_at.is_(None))
        if id_patient is not None:
            base = base.where(VitalSignsModel.id_patient == id_patient)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._session.execute(count_stmt)).scalar_one()

        data_stmt = base.order_by(VitalSignsModel.enregistre_le.desc()).offset(params.offset).limit(params.per_page)
        result = await self._session.execute(data_stmt)
        return [_to_entity(m) for m in result.scalars().all()], total

    async def get_by_id(self, vital_id: int) -> Optional[VitalSigns]:
        stmt = select(VitalSignsModel).where(VitalSignsModel.id == vital_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _to_entity(m) if m else None

    async def create(
        self,
        id_patient: int,
        enregistre_par: Optional[int] = None,
        id_rendez_vous: Optional[int] = None,
        tension_systolique: Optional[int] = None,
        tension_diastolique: Optional[int] = None,
        frequence_cardiaque: Optional[int] = None,
        temperature: Optional[Decimal] = None,
        poids: Optional[Decimal] = None,
        taille: Optional[Decimal] = None,
        saturation_oxygene: Optional[int] = None,
        glycemie: Optional[Decimal] = None,
        notes: Optional[str] = None,
        enregistre_le: Optional[datetime] = None,
    ) -> VitalSigns:
        kwargs = dict(
            id_patient=id_patient,
            enregistre_par=enregistre_par,
            id_rendez_vous=id_rendez_vous,
            tension_systolique=tension_systolique,
            tension_diastolique=tension_diastolique,
            frequence_cardiaque=frequence_cardiaque,
            temperature=temperature,
            poids=poids,
            taille=taille,
            saturation_oxygene=saturation_oxygene,
            glycemie=glycemie,
            notes=notes,
        )
        if enregistre_le is not None:
            kwargs["enregistre_le"] = enregistre_le
        m = VitalSignsModel(**kwargs)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _to_entity(m)

    async def update(self, vital_id: int, **kwargs) -> Optional[VitalSigns]:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne.
        stmt = (
            update(VitalSignsModel)
            .where(VitalSignsModel.id == vital_id, VitalSignsModel.deleted_at.is_(None))
            .values(**kwargs)
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            return None
        m = (
            await self._session.execute(
                select(VitalSignsModel).where(VitalSignsModel.id == vital_id)
            )
        ).scalar_one_or_none()
        return _to_entity(m) if m else None

    async def soft_delete(self, vital_id: int) -> bool:
        stmt = (
            update(VitalSignsModel)
            .where(VitalSignsModel.id == vital_id, VitalSignsModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def get_stats(self, id_patient: int) -> VitalStats:
        """Récupère la dernière valeur de chaque type de constante vitale."""
        requete = (
            select(VitalSignsModel)
            .where(
                VitalSignsModel.id_patient == id_patient,
                VitalSignsModel.deleted_at.is_(None),
            )
            .order_by(VitalSignsModel.enregistre_le.desc())
            .limit(50)  # suffisant pour extraire les dernières valeurs de chaque type
        )
        resultat = await self._session.execute(requete)
        enregistrements = resultat.scalars().all()

        statistiques = VitalStats(id_patient=id_patient)
        for m in enregistrements:
            if statistiques.last_blood_pressure_systolic is None and m.tension_systolique is not None:
                statistiques.last_blood_pressure_systolic = m.tension_systolique
            if statistiques.last_blood_pressure_diastolic is None and m.tension_diastolique is not None:
                statistiques.last_blood_pressure_diastolic = m.tension_diastolique
            if statistiques.last_heart_rate is None and m.frequence_cardiaque is not None:
                statistiques.last_heart_rate = m.frequence_cardiaque
            if statistiques.last_temperature is None and m.temperature is not None:
                statistiques.last_temperature = m.temperature
            if statistiques.last_weight is None and m.poids is not None:
                statistiques.last_weight = m.poids
            if statistiques.last_height is None and m.taille is not None:
                statistiques.last_height = m.taille
            if statistiques.last_oxygen_saturation is None and m.saturation_oxygene is not None:
                statistiques.last_oxygen_saturation = m.saturation_oxygene
            if statistiques.last_blood_sugar is None and m.glycemie is not None:
                statistiques.last_blood_sugar = m.glycemie

        # Calcul de l'IMC à partir des dernières valeurs
        if statistiques.last_weight is not None and statistiques.last_height is not None and statistiques.last_height > 0:
            taille_m = float(statistiques.last_height) / 100.0
            statistiques.last_bmi = round(float(statistiques.last_weight) / (taille_m ** 2), 2)

        return statistiques
