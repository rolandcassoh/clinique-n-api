"""Implémentations SQLAlchemy async des dépôts — module rendez-vous."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.rendez_vous.domain.entites import (
    Appointment,
    AppointmentStatus,
    AppointmentTransaction,
    AppointmentType,
    PaymentStatus,
)
from app.modules.rendez_vous.domain.depots import (
    AppointmentRepository,
    AppointmentTransactionRepository,
)
from app.modules.rendez_vous.infrastructure.modeles import (
    AppointmentModel,
    AppointmentTransactionModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Convertisseurs modèle → entité
# ---------------------------------------------------------------------------


def _appointment_to_entity(m: AppointmentModel) -> Appointment:
    return Appointment(
        id=m.id,
        reference=m.reference,
        id_clinique=m.id_clinique,
        id_medecin=m.id_medecin,
        id_patient=m.id_patient,
        programme_le=m.programme_le,
        duree_minutes=m.duree_minutes,
        statut=AppointmentStatus(m.statut),
        type=AppointmentType(m.type),
        montant=m.montant,
        montant_avance=m.montant_avance,
        statut_paiement=PaymentStatus(m.statut_paiement),
        passerelle_paiement=m.passerelle_paiement,
        reference_paiement=m.reference_paiement,
        notes=m.notes,
        motif_annulation=m.motif_annulation,
        id_evenement_google=m.id_evenement_google,
        est_suivi=m.est_suivi,
        id_rdv_parent=m.id_rdv_parent,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _transaction_to_entity(m: AppointmentTransactionModel) -> AppointmentTransaction:
    return AppointmentTransaction(
        id=m.id,
        id_rendez_vous=m.id_rendez_vous,
        montant=m.montant,
        devise=m.devise,
        passerelle=m.passerelle,
        reference_transaction=m.reference_transaction,
        statut=m.statut,
        reponse_passerelle=m.reponse_passerelle,
        created_at=m.created_at or datetime.utcnow(),
        updated_at=m.updated_at or datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Dépôt SQLAlchemy pour les rendez-vous
# ---------------------------------------------------------------------------


class SQLAlchemyAppointmentRepository(AppointmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, appointment: Appointment) -> Appointment:
        if appointment.id == 0:
            # Nouvelle création
            now = datetime.utcnow()
            model = AppointmentModel(
                reference=appointment.reference,
                id_clinique=appointment.id_clinique,
                id_medecin=appointment.id_medecin,
                id_patient=appointment.id_patient,
                programme_le=appointment.programme_le,
                duree_minutes=appointment.duree_minutes,
                statut=appointment.statut.valeur,
                type=appointment.type.valeur,
                montant=appointment.montant,
                montant_avance=appointment.montant_avance,
                statut_paiement=appointment.statut_paiement.valeur,
                passerelle_paiement=appointment.passerelle_paiement,
                reference_paiement=appointment.reference_paiement,
                notes=appointment.notes,
                est_suivi=appointment.est_suivi,
                id_rdv_parent=appointment.id_rdv_parent,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return _appointment_to_entity(model)
        else:
            # Mise à jour d'un rendez-vous existant
            q = select(AppointmentModel).where(
                AppointmentModel.id == appointment.id,
                AppointmentModel.deleted_at.is_(None),
            )
            model = (await self._session.execute(q)).scalar_one_or_none()
            if model is None:
                raise ValueError(f"Rendez-vous {appointment.id} introuvable pour la mise à jour")
            model.statut = appointment.statut.valeur
            model.type = appointment.type.valeur
            model.statut_paiement = appointment.statut_paiement.valeur
            model.passerelle_paiement = appointment.passerelle_paiement
            model.reference_paiement = appointment.reference_paiement
            model.motif_annulation = appointment.motif_annulation
            model.notes = appointment.notes
            model.id_evenement_google = appointment.id_evenement_google
            model.montant_avance = appointment.montant_avance
            await self._session.flush()
            await self._session.refresh(model)
            return _appointment_to_entity(model)

    async def find_by_id(self, id_rendez_vous: int) -> Optional[Appointment]:
        q = select(AppointmentModel).where(
            AppointmentModel.id == id_rendez_vous,
            AppointmentModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _appointment_to_entity(row) if row else None

    async def find_by_reference(self, reference: str) -> Optional[Appointment]:
        q = select(AppointmentModel).where(
            AppointmentModel.reference == reference,
            AppointmentModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _appointment_to_entity(row) if row else None

    async def list_for_patient(
        self,
        id_patient: int,
        params: PaginationParams,
        statut: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.id_patient == id_patient,
            AppointmentModel.deleted_at.is_(None),
        )
        if statut:
            base_q = base_q.where(AppointmentModel.statut == statut)
        if date_from:
            base_q = base_q.where(AppointmentModel.programme_le >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.programme_le <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.programme_le.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def list_for_doctor(
        self,
        id_medecin: int,
        params: PaginationParams,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.id_medecin == id_medecin,
            AppointmentModel.deleted_at.is_(None),
        )
        if statut:
            base_q = base_q.where(AppointmentModel.statut == statut)
        if date_from:
            base_q = base_q.where(AppointmentModel.programme_le >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.programme_le <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.programme_le.asc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def list_all(
        self,
        params: PaginationParams,
        statut: Optional[str] = None,
        id_medecin: Optional[int] = None,
        id_patient: Optional[int] = None,
        id_clinique: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.deleted_at.is_(None)
        )
        if statut:
            base_q = base_q.where(AppointmentModel.statut == statut)
        if id_medecin:
            base_q = base_q.where(AppointmentModel.id_medecin == id_medecin)
        if id_patient:
            base_q = base_q.where(AppointmentModel.id_patient == id_patient)
        if id_clinique:
            base_q = base_q.where(AppointmentModel.id_clinique == id_clinique)
        if date_from:
            base_q = base_q.where(AppointmentModel.programme_le >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.programme_le <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.programme_le.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def get_booked_slots(self, id_medecin: int, day: date) -> list[datetime]:
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
        q = select(AppointmentModel.programme_le).where(
            AppointmentModel.id_medecin == id_medecin,
            AppointmentModel.programme_le >= day_start,
            AppointmentModel.programme_le <= day_end,
            AppointmentModel.statut.in_(["pending", "confirmed"]),
            AppointmentModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(q)).scalars().all()
        return list(rows)

    async def count_by_status(self, id_clinique: Optional[int] = None) -> dict[str, int]:
        q = select(AppointmentModel.statut, func.count().label("cnt")).where(
            AppointmentModel.deleted_at.is_(None)
        )
        if id_clinique:
            q = q.where(AppointmentModel.id_clinique == id_clinique)
        q = q.group_by(AppointmentModel.statut)
        rows = (await self._session.execute(q)).all()
        return {row[0]: row[1] for row in rows}

    async def sum_revenue(
        self,
        id_clinique: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        q = select(func.coalesce(func.sum(AppointmentModel.montant), 0)).where(
            AppointmentModel.deleted_at.is_(None),
            AppointmentModel.statut_paiement == "paid",
        )
        if id_clinique:
            q = q.where(AppointmentModel.id_clinique == id_clinique)
        if date_from:
            q = q.where(AppointmentModel.programme_le >= date_from)
        if date_to:
            q = q.where(AppointmentModel.programme_le <= date_to)
        result = (await self._session.execute(q)).scalar_one()
        return Decimal(str(result))

    async def soft_delete(self, id_rendez_vous: int) -> bool:
        q = select(AppointmentModel).where(
            AppointmentModel.id == id_rendez_vous,
            AppointmentModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# Dépôt SQLAlchemy pour les transactions de rendez-vous
# ---------------------------------------------------------------------------


class SQLAlchemyAppointmentTransactionRepository(AppointmentTransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        id_rendez_vous: int,
        montant: Decimal,
        devise: str,
        passerelle: str,
        reference_transaction: str,
        statut: str,
        reponse_passerelle: Optional[dict] = None,
    ) -> AppointmentTransaction:
        now = datetime.utcnow()
        tx = AppointmentTransactionModel(
            id_rendez_vous=id_rendez_vous,
            montant=montant,
            devise=devise,
            passerelle=passerelle,
            reference_transaction=reference_transaction,
            statut=statut,
            reponse_passerelle=reponse_passerelle,
            created_at=now,
            updated_at=now,
        )
        self._session.add(tx)
        await self._session.flush()
        await self._session.refresh(tx)
        return _transaction_to_entity(tx)

    async def list_for_appointment(
        self, id_rendez_vous: int
    ) -> list[AppointmentTransaction]:
        q = (
            select(AppointmentTransactionModel)
            .where(AppointmentTransactionModel.id_rendez_vous == id_rendez_vous)
            .order_by(AppointmentTransactionModel.created_at.desc())
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_transaction_to_entity(r) for r in rows]

    async def update_status(
        self,
        reference_transaction: str,
        statut: str,
        reponse_passerelle: Optional[dict] = None,
    ) -> Optional[AppointmentTransaction]:
        q = select(AppointmentTransactionModel).where(
            AppointmentTransactionModel.reference_transaction == reference_transaction
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.statut = statut
        row.updated_at = datetime.utcnow()
        if reponse_passerelle is not None:
            row.reponse_passerelle = reponse_passerelle
        await self._session.flush()
        await self._session.refresh(row)
        return _transaction_to_entity(row)
