"""Implémentations SQLAlchemy async des repositories billing."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.domain.entities import (
    BillingItem,
    BillingRecord,
    BillingStatus,
)
from app.modules.billing.domain.repositories import BillingRepository
from app.modules.billing.infrastructure.models import BillingItemModel, BillingRecordModel
from app.shared.schemas.pagination import PaginationParams


def _item_to_entity(m: BillingItemModel) -> BillingItem:
    return BillingItem(
        id=m.id,
        billing_id=m.billing_id,
        description=m.description,
        quantity=m.quantity,
        unit_price=Decimal(str(m.unit_price)),
        subtotal=Decimal(str(m.subtotal)),
        tax_rate=Decimal(str(m.tax_rate)),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _record_to_entity(m: BillingRecordModel) -> BillingRecord:
    return BillingRecord(
        id=m.id,
        appointment_id=m.appointment_id,
        patient_id=m.patient_id,
        reference=m.reference,
        subtotal=Decimal(str(m.subtotal)),
        discount_amount=Decimal(str(m.discount_amount)),
        tax_amount=Decimal(str(m.tax_amount)),
        total=Decimal(str(m.total)),
        status=BillingStatus(m.status),
        items=[_item_to_entity(i) for i in (m.items or [])],
        due_date=m.due_date,
        paid_at=m.paid_at,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyBillingRepository(BillingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, billing_id: int) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.id == billing_id,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _record_to_entity(row) if row else None

    async def get_by_appointment(self, appointment_id: int) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.appointment_id == appointment_id,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _record_to_entity(row) if row else None

    async def create(
        self,
        appointment_id: int,
        patient_id: int,
        reference: str,
        subtotal: Decimal,
        discount_amount: Decimal,
        tax_amount: Decimal,
        total: Decimal,
        items: list[dict],
        due_date: Optional[object] = None,
        notes: Optional[str] = None,
    ) -> BillingRecord:
        record = BillingRecordModel(
            appointment_id=appointment_id,
            patient_id=patient_id,
            reference=reference,
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            total=total,
            status="draft",
            due_date=due_date,
            notes=notes,
        )
        self._session.add(record)
        await self._session.flush()

        for item_data in items:
            q = int(item_data.get("quantity", 1))
            up = Decimal(str(item_data["unit_price"]))
            sub = Decimal(str(item_data.get("subtotal", float(q * up))))
            tr = Decimal(str(item_data.get("tax_rate", 0)))
            billing_item = BillingItemModel(
                billing_id=record.id,
                description=item_data["description"],
                quantity=q,
                unit_price=up,
                subtotal=sub,
                tax_rate=tr,
            )
            self._session.add(billing_item)

        await self._session.flush()
        await self._session.refresh(record)
        return _record_to_entity(record)

    async def update_status(
        self, billing_id: int, status: str, paid_at: Optional[object] = None
    ) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.id == billing_id,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.status = status
        if paid_at is not None:
            row.paid_at = paid_at
        await self._session.flush()
        await self._session.refresh(row)
        return _record_to_entity(row)

    async def list_by_patient(
        self, patient_id: int, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]:
        base = select(BillingRecordModel).where(
            BillingRecordModel.patient_id == patient_id,
            BillingRecordModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(BillingRecordModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_record_to_entity(r) for r in rows], total

    async def list_all(
        self, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]:
        base = select(BillingRecordModel).where(BillingRecordModel.deleted_at.is_(None))
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(BillingRecordModel.created_at.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_record_to_entity(r) for r in rows], total

    async def get_stats(self) -> dict:
        # Total des factures payées
        paid_total = (
            await self._session.execute(
                select(func.sum(BillingRecordModel.total)).where(
                    BillingRecordModel.status == "paid",
                    BillingRecordModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none() or 0

        # Total des factures émises (en attente)
        issued_total = (
            await self._session.execute(
                select(func.sum(BillingRecordModel.total)).where(
                    BillingRecordModel.status == "issued",
                    BillingRecordModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none() or 0

        # Comptage par statut
        count_result = (
            await self._session.execute(
                select(BillingRecordModel.status, func.count(BillingRecordModel.id))
                .where(BillingRecordModel.deleted_at.is_(None))
                .group_by(BillingRecordModel.status)
            )
        ).all()

        counts_by_status = {row[0]: row[1] for row in count_result}

        return {
            "total_paid": float(paid_total),
            "total_issued": float(issued_total),
            "counts_by_status": counts_by_status,
        }
