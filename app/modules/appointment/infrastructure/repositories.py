"""Implémentations SQLAlchemy async des repositories du module appointment."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.appointment.domain.entities import (
    Appointment,
    AppointmentStatus,
    AppointmentTransaction,
    AppointmentType,
    PaymentStatus,
)
from app.modules.appointment.domain.repositories import (
    AppointmentRepository,
    AppointmentTransactionRepository,
)
from app.modules.appointment.infrastructure.models import (
    AppointmentModel,
    AppointmentTransactionModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------


def _appointment_to_entity(m: AppointmentModel) -> Appointment:
    return Appointment(
        id=m.id,
        reference=m.reference,
        clinic_id=m.clinic_id,
        doctor_id=m.doctor_id,
        patient_id=m.patient_id,
        scheduled_at=m.scheduled_at,
        duration_minutes=m.duration_minutes,
        status=AppointmentStatus(m.status),
        type=AppointmentType(m.type),
        amount=m.amount,
        advance_amount=m.advance_amount,
        payment_status=PaymentStatus(m.payment_status),
        payment_gateway=m.payment_gateway,
        payment_reference=m.payment_reference,
        notes=m.notes,
        cancellation_reason=m.cancellation_reason,
        google_event_id=m.google_event_id,
        is_followup=m.is_followup,
        parent_appointment_id=m.parent_appointment_id,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _transaction_to_entity(m: AppointmentTransactionModel) -> AppointmentTransaction:
    return AppointmentTransaction(
        id=m.id,
        appointment_id=m.appointment_id,
        amount=m.amount,
        currency=m.currency,
        gateway=m.gateway,
        transaction_ref=m.transaction_ref,
        status=m.status,
        gateway_response=m.gateway_response,
        created_at=m.created_at or datetime.utcnow(),
        updated_at=m.updated_at or datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# SQLAlchemyAppointmentRepository
# ---------------------------------------------------------------------------


class SQLAlchemyAppointmentRepository(AppointmentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, appointment: Appointment) -> Appointment:
        if appointment.id == 0:
            # Création
            now = datetime.utcnow()
            model = AppointmentModel(
                reference=appointment.reference,
                clinic_id=appointment.clinic_id,
                doctor_id=appointment.doctor_id,
                patient_id=appointment.patient_id,
                scheduled_at=appointment.scheduled_at,
                duration_minutes=appointment.duration_minutes,
                status=appointment.status.value,
                type=appointment.type.value,
                amount=appointment.amount,
                advance_amount=appointment.advance_amount,
                payment_status=appointment.payment_status.value,
                payment_gateway=appointment.payment_gateway,
                payment_reference=appointment.payment_reference,
                notes=appointment.notes,
                is_followup=appointment.is_followup,
                parent_appointment_id=appointment.parent_appointment_id,
            )
            self._session.add(model)
            await self._session.flush()
            await self._session.refresh(model)
            return _appointment_to_entity(model)
        else:
            # Mise à jour
            q = select(AppointmentModel).where(
                AppointmentModel.id == appointment.id,
                AppointmentModel.deleted_at.is_(None),
            )
            model = (await self._session.execute(q)).scalar_one_or_none()
            if model is None:
                raise ValueError(f"Appointment {appointment.id} not found for update")
            model.status = appointment.status.value
            model.type = appointment.type.value
            model.payment_status = appointment.payment_status.value
            model.payment_gateway = appointment.payment_gateway
            model.payment_reference = appointment.payment_reference
            model.cancellation_reason = appointment.cancellation_reason
            model.notes = appointment.notes
            model.google_event_id = appointment.google_event_id
            model.advance_amount = appointment.advance_amount
            await self._session.flush()
            await self._session.refresh(model)
            return _appointment_to_entity(model)

    async def find_by_id(self, appointment_id: int) -> Optional[Appointment]:
        q = select(AppointmentModel).where(
            AppointmentModel.id == appointment_id,
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
        patient_id: int,
        params: PaginationParams,
        status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.patient_id == patient_id,
            AppointmentModel.deleted_at.is_(None),
        )
        if status:
            base_q = base_q.where(AppointmentModel.status == status)
        if date_from:
            base_q = base_q.where(AppointmentModel.scheduled_at >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.scheduled_at <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.scheduled_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def list_for_doctor(
        self,
        doctor_id: int,
        params: PaginationParams,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.doctor_id == doctor_id,
            AppointmentModel.deleted_at.is_(None),
        )
        if status:
            base_q = base_q.where(AppointmentModel.status == status)
        if date_from:
            base_q = base_q.where(AppointmentModel.scheduled_at >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.scheduled_at <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.scheduled_at.asc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def list_all(
        self,
        params: PaginationParams,
        status: Optional[str] = None,
        doctor_id: Optional[int] = None,
        patient_id: Optional[int] = None,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> tuple[list[Appointment], int]:
        base_q = select(AppointmentModel).where(
            AppointmentModel.deleted_at.is_(None)
        )
        if status:
            base_q = base_q.where(AppointmentModel.status == status)
        if doctor_id:
            base_q = base_q.where(AppointmentModel.doctor_id == doctor_id)
        if patient_id:
            base_q = base_q.where(AppointmentModel.patient_id == patient_id)
        if clinic_id:
            base_q = base_q.where(AppointmentModel.clinic_id == clinic_id)
        if date_from:
            base_q = base_q.where(AppointmentModel.scheduled_at >= date_from)
        if date_to:
            base_q = base_q.where(AppointmentModel.scheduled_at <= date_to)

        total: int = (
            await self._session.execute(
                select(func.count()).select_from(base_q.subquery())
            )
        ).scalar_one()
        rows = (
            await self._session.execute(
                base_q.order_by(AppointmentModel.scheduled_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_appointment_to_entity(r) for r in rows], total

    async def get_booked_slots(self, doctor_id: int, day: date) -> list[datetime]:
        day_start = datetime(day.year, day.month, day.day, 0, 0, 0)
        day_end = datetime(day.year, day.month, day.day, 23, 59, 59)
        q = select(AppointmentModel.scheduled_at).where(
            AppointmentModel.doctor_id == doctor_id,
            AppointmentModel.scheduled_at >= day_start,
            AppointmentModel.scheduled_at <= day_end,
            AppointmentModel.status.in_(["pending", "confirmed"]),
            AppointmentModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(q)).scalars().all()
        return list(rows)

    async def count_by_status(self, clinic_id: Optional[int] = None) -> dict[str, int]:
        q = select(AppointmentModel.status, func.count().label("cnt")).where(
            AppointmentModel.deleted_at.is_(None)
        )
        if clinic_id:
            q = q.where(AppointmentModel.clinic_id == clinic_id)
        q = q.group_by(AppointmentModel.status)
        rows = (await self._session.execute(q)).all()
        return {row[0]: row[1] for row in rows}

    async def sum_revenue(
        self,
        clinic_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> Decimal:
        q = select(func.coalesce(func.sum(AppointmentModel.amount), 0)).where(
            AppointmentModel.deleted_at.is_(None),
            AppointmentModel.payment_status == "paid",
        )
        if clinic_id:
            q = q.where(AppointmentModel.clinic_id == clinic_id)
        if date_from:
            q = q.where(AppointmentModel.scheduled_at >= date_from)
        if date_to:
            q = q.where(AppointmentModel.scheduled_at <= date_to)
        result = (await self._session.execute(q)).scalar_one()
        return Decimal(str(result))

    async def soft_delete(self, appointment_id: int) -> bool:
        q = select(AppointmentModel).where(
            AppointmentModel.id == appointment_id,
            AppointmentModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# SQLAlchemyAppointmentTransactionRepository
# ---------------------------------------------------------------------------


class SQLAlchemyAppointmentTransactionRepository(AppointmentTransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        appointment_id: int,
        amount: Decimal,
        currency: str,
        gateway: str,
        transaction_ref: str,
        status: str,
        gateway_response: Optional[dict] = None,
    ) -> AppointmentTransaction:
        now = datetime.utcnow()
        tx = AppointmentTransactionModel(
            appointment_id=appointment_id,
            amount=amount,
            currency=currency,
            gateway=gateway,
            transaction_ref=transaction_ref,
            status=status,
            gateway_response=gateway_response,
            created_at=now,
            updated_at=now,
        )
        self._session.add(tx)
        await self._session.flush()
        await self._session.refresh(tx)
        return _transaction_to_entity(tx)

    async def list_for_appointment(
        self, appointment_id: int
    ) -> list[AppointmentTransaction]:
        q = (
            select(AppointmentTransactionModel)
            .where(AppointmentTransactionModel.appointment_id == appointment_id)
            .order_by(AppointmentTransactionModel.created_at.desc())
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_transaction_to_entity(r) for r in rows]

    async def update_status(
        self,
        transaction_ref: str,
        status: str,
        gateway_response: Optional[dict] = None,
    ) -> Optional[AppointmentTransaction]:
        q = select(AppointmentTransactionModel).where(
            AppointmentTransactionModel.transaction_ref == transaction_ref
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.status = status
        row.updated_at = datetime.utcnow()
        if gateway_response is not None:
            row.gateway_response = gateway_response
        await self._session.flush()
        await self._session.refresh(row)
        return _transaction_to_entity(row)
