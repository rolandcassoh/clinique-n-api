"""Implémentations SQLAlchemy async des repositories commission."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.commission.domain.entites import (
    CommissionEarning,
    CommissionStatus,
    CommissionType,
    EmployeeCommission,
    EmployeeEarning,
    EarningStatus,
)
from app.modules.commission.domain.depots import (
    CommissionEarningRepository,
    CommissionRateRepository,
    EmployeeEarningRepository,
)
from app.modules.commission.infrastructure.modeles import (
    CommissionEarningModel,
    EmployeeCommissionModel,
    EmployeeEarningModel,
)
from app.shared.schemas.pagination import PaginationParams


def _rate_to_entity(m: EmployeeCommissionModel) -> EmployeeCommission:
    return EmployeeCommission(
        id=m.id,
        id_clinique=m.id_clinique,
        id_medecin=m.id_medecin,
        taux_commission=Decimal(str(m.taux_commission)),
        type=CommissionType(m.type),
        est_actif=m.est_actif,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _earning_to_entity(m: CommissionEarningModel) -> CommissionEarning:
    return CommissionEarning(
        id=m.id,
        id_rendez_vous=m.id_rendez_vous,
        id_clinique=m.id_clinique,
        id_medecin=m.id_medecin,
        montant_rdv=Decimal(str(m.montant_rdv)),
        taux_commission=Decimal(str(m.taux_commission)),
        montant_commission=Decimal(str(m.montant_commission)),
        gain_medecin=Decimal(str(m.gain_medecin)),
        statut=CommissionStatus(m.statut),
        paye_le=m.paye_le,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _emp_earning_to_entity(m: EmployeeEarningModel) -> EmployeeEarning:
    return EmployeeEarning(
        id=m.id,
        id_medecin=m.id_medecin,
        debut_periode=m.debut_periode,
        fin_periode=m.fin_periode,
        total_rdv=m.total_rdv,
        montant_brut=Decimal(str(m.montant_brut)),
        commission_deduite=Decimal(str(m.commission_deduite)),
        montant_net=Decimal(str(m.montant_net)),
        statut=EarningStatus(m.statut),
        paye_le=m.paye_le,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyCommissionRateRepository(CommissionRateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_doctor(
        self, id_clinique: int, id_medecin: int
    ) -> Optional[EmployeeCommission]:
        # Chercher d'abord un taux spécifique au médecin
        requete = select(EmployeeCommissionModel).where(
            EmployeeCommissionModel.id_clinique == id_clinique,
            EmployeeCommissionModel.id_medecin == id_medecin,
            EmployeeCommissionModel.est_actif.is_(True),
            EmployeeCommissionModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne:
            return _rate_to_entity(ligne)

        # Repli : taux général de la clinique (id_medecin IS NULL)
        requete_generale = select(EmployeeCommissionModel).where(
            EmployeeCommissionModel.id_clinique == id_clinique,
            EmployeeCommissionModel.id_medecin.is_(None),
            EmployeeCommissionModel.est_actif.is_(True),
            EmployeeCommissionModel.deleted_at.is_(None),
        )
        ligne_generale = (await self._session.execute(requete_generale)).scalar_one_or_none()
        return _rate_to_entity(ligne_generale) if ligne_generale else None

    async def list_all(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        id_medecin: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]:
        # Ce dépôt gère les taux de commission, pas les revenus — déléguer à CommissionEarningRepository
        return [], 0


class SQLAlchemyCommissionEarningRepository(CommissionEarningRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        id_rendez_vous: int,
        id_clinique: int,
        id_medecin: int,
        montant_rdv: Decimal,
        taux_commission: Decimal,
        montant_commission: Decimal,
        gain_medecin: Decimal,
    ) -> CommissionEarning:
        earning = CommissionEarningModel(
            id_rendez_vous=id_rendez_vous,
            id_clinique=id_clinique,
            id_medecin=id_medecin,
            montant_rdv=montant_rdv,
            taux_commission=taux_commission,
            montant_commission=montant_commission,
            gain_medecin=gain_medecin,
            statut="pending",
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
        row.statut = "paid"
        row.paye_le = datetime.utcnow()
        await self._session.flush()
        await self._session.refresh(row)
        return _earning_to_entity(row)

    async def list_all(
        self,
        params: PaginationParams,
        id_clinique: Optional[int] = None,
        id_medecin: Optional[int] = None,
        statut: Optional[str] = None,
    ) -> tuple[list[CommissionEarning], int]:
        base = select(CommissionEarningModel).where(
            CommissionEarningModel.deleted_at.is_(None)
        )
        if id_clinique is not None:
            base = base.where(CommissionEarningModel.id_clinique == id_clinique)
        if id_medecin is not None:
            base = base.where(CommissionEarningModel.id_medecin == id_medecin)
        if statut is not None:
            base = base.where(CommissionEarningModel.statut == statut)

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
        self, id_medecin: int, params: PaginationParams
    ) -> tuple[list[CommissionEarning], int]:
        return await self.list_all(params, id_medecin=id_medecin)

    async def get_summary_for_doctor(self, id_medecin: int) -> dict:
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.id_medecin == id_medecin,
            CommissionEarningModel.deleted_at.is_(None),
        )
        lignes = (await self._session.execute(q)).scalars().all()

        montant_brut = sum(Decimal(str(r.montant_rdv)) for r in lignes)
        total_commissions = sum(Decimal(str(r.montant_commission)) for r in lignes)
        montant_net = sum(Decimal(str(r.gain_medecin)) for r in lignes)

        return {
            "total_rdv": len(lignes),
            "montant_brut": float(montant_brut),
            "total_commissions": float(total_commissions),
            "montant_net": float(montant_net),
        }


class SQLAlchemyEmployeeEarningRepository(EmployeeEarningRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def generate_for_period(
        self,
        id_medecin: int,
        id_clinique: int,
        debut_periode: date,
        fin_periode: date,
    ) -> EmployeeEarning:
        # Agréger les commissions pour la période
        q = select(CommissionEarningModel).where(
            CommissionEarningModel.id_medecin == id_medecin,
            CommissionEarningModel.id_clinique == id_clinique,
            CommissionEarningModel.deleted_at.is_(None),
            CommissionEarningModel.created_at >= datetime.combine(debut_periode, datetime.min.time()),  # type: ignore[attr-defined]
            CommissionEarningModel.created_at <= datetime.combine(fin_periode, datetime.max.time()),  # type: ignore[attr-defined]
        )
        lignes_revenus = (await self._session.execute(q)).scalars().all()

        total_rdv = len(lignes_revenus)
        montant_brut = sum(Decimal(str(r.montant_rdv)) for r in lignes_revenus)
        commissions = sum(Decimal(str(r.montant_commission)) for r in lignes_revenus)
        montant_net = montant_brut - commissions

        revenu_employe = EmployeeEarningModel(
            id_medecin=id_medecin,
            debut_periode=debut_periode,
            fin_periode=fin_periode,
            total_rdv=total_rdv,
            montant_brut=montant_brut,
            commission_deduite=commissions,
            montant_net=montant_net,
            statut="pending",
        )
        self._session.add(revenu_employe)
        await self._session.flush()
        await self._session.refresh(revenu_employe)
        return _emp_earning_to_entity(revenu_employe)

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
                base.order_by(EmployeeEarningModel.debut_periode.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_emp_earning_to_entity(r) for r in rows], total

    async def list_by_doctor(
        self, id_medecin: int, params: PaginationParams
    ) -> tuple[list[EmployeeEarning], int]:
        base = select(EmployeeEarningModel).where(
            EmployeeEarningModel.id_medecin == id_medecin,
            EmployeeEarningModel.deleted_at.is_(None),
        )
        total: int = (
            await self._session.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()
        rows = (
            await self._session.execute(
                base.order_by(EmployeeEarningModel.debut_periode.desc())
                .offset(params.offset)
                .limit(params.per_page)
            )
        ).scalars().all()
        return [_emp_earning_to_entity(r) for r in rows], total
