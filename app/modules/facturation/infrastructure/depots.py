"""Implémentations SQLAlchemy async des repositories billing."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.facturation.domain.entites import (
    BillingItem,
    BillingRecord,
    BillingStatus,
)
from app.modules.facturation.domain.depots import BillingRepository
from app.modules.facturation.infrastructure.modeles import BillingItemModel, BillingRecordModel
from app.shared.schemas.pagination import PaginationParams


def _item_to_entity(m: BillingItemModel) -> BillingItem:
    return BillingItem(
        id=m.id,
        id_facture=m.id_facture,
        description=m.description,
        quantite=m.quantite,
        prix_unitaire=Decimal(str(m.prix_unitaire)),
        sous_total=Decimal(str(m.sous_total)),
        taux_taxe=Decimal(str(m.taux_taxe)),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _record_to_entity(m: BillingRecordModel) -> BillingRecord:
    return BillingRecord(
        id=m.id,
        id_rendez_vous=m.id_rendez_vous,
        id_patient=m.id_patient,
        reference=m.reference,
        sous_total=Decimal(str(m.sous_total)),
        montant_remise=Decimal(str(m.montant_remise)),
        montant_taxe=Decimal(str(m.montant_taxe)),
        total=Decimal(str(m.total)),
        statut=BillingStatus(m.statut),
        items=[_item_to_entity(i) for i in (m.items or [])],
        date_echeance=m.date_echeance,
        paye_le=m.paye_le,
        notes=m.notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyBillingRepository(BillingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_facture: int) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.id == id_facture,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _record_to_entity(row) if row else None

    async def get_by_appointment(self, id_rendez_vous: int) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.id_rendez_vous == id_rendez_vous,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _record_to_entity(row) if row else None

    async def create(
        self,
        id_rendez_vous: int,
        id_patient: int,
        reference: str,
        sous_total: Decimal,
        montant_remise: Decimal,
        montant_taxe: Decimal,
        total: Decimal,
        items: list[dict],
        date_echeance: Optional[object] = None,
        notes: Optional[str] = None,
    ) -> BillingRecord:
        record = BillingRecordModel(
            id_rendez_vous=id_rendez_vous,
            id_patient=id_patient,
            reference=reference,
            sous_total=sous_total,
            montant_remise=montant_remise,
            montant_taxe=montant_taxe,
            total=total,
            statut="draft",
            date_echeance=date_echeance,
            notes=notes,
        )
        self._session.add(record)
        await self._session.flush()

        for donnees_element in items:
            qte = int(donnees_element.get("quantite", 1))
            prix_unitaire = Decimal(str(donnees_element["prix_unitaire"]))
            sous_total = Decimal(str(donnees_element.get("sous_total", float(qte * prix_unitaire))))
            taux_taxe = Decimal(str(donnees_element.get("taux_taxe", 0)))
            billing_item = BillingItemModel(
                id_facture=record.id,
                description=donnees_element["description"],
                quantite=qte,
                prix_unitaire=prix_unitaire,
                sous_total=sous_total,
                taux_taxe=taux_taxe,
            )
            self._session.add(billing_item)

        await self._session.flush()
        await self._session.refresh(record)
        return _record_to_entity(record)

    async def update_status(
        self, id_facture: int, statut: str, paye_le: Optional[object] = None
    ) -> Optional[BillingRecord]:
        q = select(BillingRecordModel).where(
            BillingRecordModel.id == id_facture,
            BillingRecordModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        row.statut = statut
        if paye_le is not None:
            row.paye_le = paye_le
        await self._session.flush()
        await self._session.refresh(row)
        return _record_to_entity(row)

    async def list_by_patient(
        self, id_patient: int, params: PaginationParams
    ) -> tuple[list[BillingRecord], int]:
        base = select(BillingRecordModel).where(
            BillingRecordModel.id_patient == id_patient,
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
        total_paye = (
            await self._session.execute(
                select(func.sum(BillingRecordModel.total)).where(
                    BillingRecordModel.statut == "paid",
                    BillingRecordModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none() or 0

        # Total des factures émises (en attente de paiement)
        total_emis = (
            await self._session.execute(
                select(func.sum(BillingRecordModel.total)).where(
                    BillingRecordModel.statut == "issued",
                    BillingRecordModel.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none() or 0

        # Comptage par statut
        resultat_compte = (
            await self._session.execute(
                select(BillingRecordModel.statut, func.count(BillingRecordModel.id))
                .where(BillingRecordModel.deleted_at.is_(None))
                .group_by(BillingRecordModel.statut)
            )
        ).all()

        compte_par_statut = {ligne[0]: ligne[1] for ligne in resultat_compte}

        return {
            "total_paid": float(total_paye),
            "total_issued": float(total_emis),
            "counts_by_status": compte_par_statut,
        }
