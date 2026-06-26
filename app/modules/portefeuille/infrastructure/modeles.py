"""Modèles SQLAlchemy du module portefeuille."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.models.base import BaseModel


class PatientWalletModel(BaseModel):
    # Table BD : portefeuilles_patients
    __tablename__ = "portefeuilles_patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, unique=True)
    solde: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0"))
    devise: Mapped[str] = mapped_column(String(3), nullable=False, default="XAF")


class WalletHistoryModel(Base):
    # Table BD : historique_portefeuille
    __tablename__ = "historique_portefeuille"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_portefeuille: Mapped[int] = mapped_column(
        Integer, ForeignKey("portefeuilles_patients.id", ondelete="CASCADE"), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("credit", "debit", name="wallet_transaction_type_enum"), nullable=False
    )
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    solde_apres: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
