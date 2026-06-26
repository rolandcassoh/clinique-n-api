"""Modèles SQLAlchemy du module commissions."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class EmployeeCommissionModel(BaseModel):
    # Table BD : commissions_employés
    __tablename__ = "commissions_employes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="CASCADE"), nullable=False)
    id_medecin: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    taux_commission: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("percentage", "fixed", name="commission_type_enum"),
        nullable=False, default="percentage",
    )
    est_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class CommissionEarningModel(BaseModel):
    # Table BD : gains_commissions
    __tablename__ = "gains_commissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_rendez_vous: Mapped[int] = mapped_column(
        Integer, ForeignKey("rendez_vous.id", ondelete="RESTRICT"), nullable=False)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="RESTRICT"), nullable=False)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False)
    montant_rdv: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    taux_commission: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    montant_commission: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    gain_medecin: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum("pending", "paid", name="commission_earning_status_enum"),
        nullable=False, default="pending")
    paye_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmployeeEarningModel(BaseModel):
    # Table BD : revenus_employés
    __tablename__ = "revenus_employes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False)
    debut_periode: Mapped[date] = mapped_column(Date, nullable=False)
    fin_periode: Mapped[date] = mapped_column(Date, nullable=False)
    total_rdv: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    montant_brut: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    commission_deduite: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    montant_net: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    statut: Mapped[str] = mapped_column(
        Enum("pending", "paid", name="employee_earning_status_enum"),
        nullable=False, default="pending")
    paye_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
