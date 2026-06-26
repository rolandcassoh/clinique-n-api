"""Modèles SQLAlchemy du module facturation."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel
from app.database import Base


class BillingRecordModel(BaseModel):
    # Table BD : factures
    __tablename__ = "factures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_rendez_vous: Mapped[int] = mapped_column(
        Integer, ForeignKey("rendez_vous.id", ondelete="RESTRICT"), nullable=False)
    id_patient: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    sous_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    montant_remise: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    montant_taxe: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum("draft", "issued", "paid", "cancelled", name="billing_status_enum"),
        nullable=False, default="draft")
    date_echeance: Mapped[date | None] = mapped_column(Date, nullable=True)
    paye_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["BillingItemModel"]] = relationship(
        "BillingItemModel", back_populates="billing", cascade="all, delete-orphan", lazy="selectin"
    )


class BillingItemModel(Base):
    # Table BD : lignes_facture
    __tablename__ = "lignes_facture"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_facture: Mapped[int] = mapped_column(
        Integer, ForeignKey("factures.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sous_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    taux_taxe: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    billing: Mapped["BillingRecordModel"] = relationship("BillingRecordModel", back_populates="items")
