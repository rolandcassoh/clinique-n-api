"""Modèles SQLAlchemy du module rendez-vous."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.shared.models.base import BaseModel


class AppointmentModel(BaseModel):
    # Table BD : rendez_vous
    __tablename__ = "rendez_vous"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    id_clinique: Mapped[int] = mapped_column(Integer, nullable=False)
    id_medecin: Mapped[int] = mapped_column(Integer, nullable=False)
    id_patient: Mapped[int] = mapped_column(Integer, nullable=False)
    programme_le: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "confirmed",
            "cancelled",
            "completed",
            "no_show",
            name="appointment_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False)
    type: Mapped[str] = mapped_column(
        Enum(
            "in_person",
            "teleconsultation",
            name="appointment_type_enum",
            native_enum=False,
        ),
        default="in_person",
        nullable=False,
    )
    montant: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False)
    montant_avance: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False)
    statut_paiement: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "partial",
            "paid",
            "refunded",
            name="apt_payment_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False)
    passerelle_paiement: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_paiement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    motif_annulation: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_evenement_google: Mapped[str | None] = mapped_column(String(255), nullable=True)
    est_suivi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    id_rdv_parent: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("rendez_vous.id"), nullable=True)

    # Relations
    transactions: Mapped[list["AppointmentTransactionModel"]] = relationship(
        "AppointmentTransactionModel",
        back_populates="appointment",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    parent: Mapped["AppointmentModel | None"] = relationship(
        "AppointmentModel",
        remote_side="AppointmentModel.id",
        foreign_keys=[id_rdv_parent],
    )


class AppointmentTransactionModel(Base):
    # Table BD : transactions_rdv
    __tablename__ = "transactions_rdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_rendez_vous: Mapped[int] = mapped_column(
        Integer, ForeignKey("rendez_vous.id"), nullable=False)
    montant: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    devise: Mapped[str] = mapped_column(String(3), default="XAF", nullable=False)
    passerelle: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_transaction: Mapped[str] = mapped_column(String(255), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum(
            "pending",
            "succeeded",
            "failed",
            "refunded",
            name="apt_tx_status_enum",
            native_enum=False,
        ),
        default="pending",
        nullable=False)
    reponse_passerelle: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    appointment: Mapped["AppointmentModel"] = relationship(
        "AppointmentModel", back_populates="transactions"
    )
