"""Implémentations SQLAlchemy async des repositories commission."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commission.domain.entities import (
    CommissionEarning,
    CommissionStatus,
    CommissionType,
    EmployeeCommission,
    EmployeeEarning,
    EarningStatus,
)
from app.modules.commission.domain.repositories import (
    CommissionEarningRepository,
    CommissionRateRepository,
    EmployeeEarningRepository,
)
from app.modules.commission.infrastructure.models import (
    CommissionEarningModel,
    EmployeeCommissionModel,
    EmployeeEarningModel,
)
from app.shared.schemas.pagination import PaginationParams


def _rate_to_entity(m: EmployeeCommissionModel) -> EmployeeCommission:
    return EmployeeCommission(
        id=m.id,
        clinic_id=m.clinic_id,
        doctor_id=m.doctor_id,
        commission_rate=Decimal(str(m.commission_rate)),
        type=CommissionType(m.type),
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _earning_to_entity(m: CommissionEarningModel) -> CommissionEarning:
    return CommissionEarning(
        id=m.id,
        appointment_id=m.appointment_id,
        clinic_id=m.clinic_id,
        doctor_id=m.doctor_id,
        appointment_amount=Decimal(str(m.appointment_amount)),
        commission_rate=Decimal(str(m.commission_rate)),
        commission_amount=Decimal(str(m.commission_amount)),
        doctor_earning=Decimal(str(m.doctor_earning)),
        status=CommissionStatus(m.status),
        paid_at=m.paid_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _emp_earning_to_entity(m: EmployeeEarningModel) -> EmployeeEarning:
    return EmployeeEarning(
        id=m.id,
        doctor_id=m.doctor_id,
        period_start=m.period_start,
        period_end=m.period_end,
        total_appointments=m.total_appointments,
        gross_amount=Decimal(str(m.gross_amount)),
        commission_deducted=Decimal(str(m.commission_deducted)),
        net_amount=Decimal(str(m.net_amount)),
        status=EarningStatus(m.status),
        paid_at=m.paid_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyCommissionRateRepository(CommissionRateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_doctor(
        self, clinic_id: int, doctor_id: int
    ) -> Optional[EmployeeCommission]:
        # D'abord chercher un taux spécifique au médecin
        q = select(EmployeeCommissionModel).where(
            EmployeeCommissionModel.clinic_id == clinic_id,
            EmployeeCommissionModel.doctor_id == doctor_id,
            EmployeeCommissionModel.is_active.is_(True),
            EmployeeCommissionModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row:
            return _rate_to_entity(row)

        # Fallback : taux général de la clinique (doctor_id IS NULL)
        q_general = select(EmployeeCommissionModel).where(
            EmployeeCommissionModel.clinic_id == clinic_id,
            EmployeeCommissionModel.doctor_id.is_(None),
            EmployeeCommissionModel.is_active.is_(True),
            EmployeeCommissionModel.deleted_at.is_(None),
        )
        row_gen = (await self._session.execute(q_general)).scalar_one_or_none()
        return _rate_to_entity(row_gen) if row_gen else None

    async def list_all(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]:
        # Ce repo gère les taux, pas les earnings — déléguer à CommissionEarningRepository
        return [], 0


class SQLAlchemyCommissionEarningRepository(CommissionEarningRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        appointment_id: int,
        clinic_id: int,
        doctor_id: int,
        appointment_amount: Decimal,
        commission_rate: Decimal,
        commission_amount: Decimal,
        doctor_earning: Decimal,
    ) -> CommissionEarning:
        earning = CommissionEarningModel(
            appointment_id=appointment_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            appointment_amount=appointment_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            doctor_earning=doctor_earning,
            status="pending",
        )
        self._session.add(earning)
        await self._session.flush()
        await self._session.refresh(earning)
        return _earning_to_entity(earning)

    async def get_by_id(self, earning_id: int) -> Optional[CommissionEarning]:
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.id == earning_id,
            CommissionEarningModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _earning_to_entity(row) if row else None

    async def mark_paid(self, earning_id: int) -> Optional[CommissionEarning]:
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.id == earning_id,
            CommissionEarningModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.status = "paid"
        row.paid_at = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(row)
        return _earning_to_entity(row)

    async def list_all(
        self,
        params: PaginationParams,
        clinic_id: Optional[int] = None,
        doctor_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]:
        base = select(CommissionEarningModel).where(
            CommissionEarningModel.deleted_at.is_(None)
        )
        if clinic_id is not None:
            base = base.where(CommissionEarningModel.clinic_id == clinic_id)
        if doctor_id is not None:
            base = base.where(CommissionEarningModel.doctor_id == doctor_id)
        if status is not None:
            base = base.where(CommissionEarningModel.status == status)

        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(CommissionEarningModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_earning_to_entity(r) for r in rows], total

    async def list_by_doctor(
        self, doctor_id: int, params: PaginationParams
    ) -> tuple[list[CommissionEarning], int]:
        return await self.list_all(params, doctor_id=doctor_id)

    async def get_summary_for_doctor(self, doctor_id: int) -> dict:
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.doctor_id == doctor_id,
            CommissionEarningModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(q)).scalars().all()

        gross = sum(Decimal(str(r.appointment_amount)) for r in rows)
        commissions = sum(Decimal(str(r.commission_amount)) for r in rows)
        net = sum(Decimal(str(r.doctor_earning)) for r in rows)

        return {
            "total_appointments": len(rows),
            "gross_amount": float(gross),
            "total_commissions": float(commissions),
            "net_amount": float(net),
        }


class SQLAlchemyEmployeeEarningRepository(EmployeeEarningRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_for_period(
        self,
        doctor_id: int,
        clinic_id: int,
        period_start: date,
        period_end: date,
    ) -> EmployeeEarning:
        # Agréger les commissions pour la période
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.doctor_id == doctor_id,
            CommissionEarningModel.clinic_id == clinic_id,
            CommissionEarningModel.deleted_at.is_(None),
            CommissionEarningModel.created_at >= datetime.combine(period_start, datetime.min.time()),  # type: ignore[attr-defined]
            CommissionEarningModel.created_at <= datetime.combine(period_end, datetime.max.time()),  # type: ignore[attr-defined]
        )
        earnings_rows = (await self._session.execute(q)).scalars().all()

        total_apts = len(earnings_rows)
        gross = sum(Decimal(str(r.appointment_amount)) for r in earnings_rows)
        commissions = sum(Decimal(str(r.commission_amount)) for r in earnings_rows)
        net = gross - commissions

        emp_earning = EmployeeEarningModel(
            doctor_id=doctor_id,
            period_start=period_start,
            period_end=period_end,
            total_appointments=total_apts,
            gross_amount=gross,
            commission_deducted=commissions,
            net_amount=net,
            status="pending",
        )
        self._session.add(emp_earning)
        await self._session.flush()
        await self._session.refresh(emp_earning)
        return _emp_earning_to_entity(emp_earning)

    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]:
        base = select(EmployeeEarningModel).where(
            EmployeeEarningModel.deleted_at.is_(None)
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(EmployeeEarningModel.period_start.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_emp_earning_to_entity(r) for r in rows], total

    async def list_by_doctor(
        self, doctor_id: int, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]:
        base = select(EmployeeEarningModel).where(
            EmployeeEarningModel.doctor_id == doctor_id,
            EmployeeEarningModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(EmployeeEarningModel.period_start.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_emp_earning_to_entity(r) for r in rows], total
