"""Modèles SQLAlchemy du module consultations médicales."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.core.crypto.field_encryption import FieldEncryption
from app.shared.models.base import BaseModel
from app.database import Base


# ---------------------------------------------------------------------------
# Type SQLAlchemy chiffré
# ---------------------------------------------------------------------------

class EncryptedText(TypeDecorator):
    """Type SQLAlchemy qui chiffre/déchiffre automatiquement via FieldEncryption."""
    impl = String(2000)
    cache_ok = True

    def process_bind_param(self, valeur: str | None, dialect) -> str | None:  # type: ignore[override]
        return FieldEncryption.encrypt(valeur) if valeur else None

    def process_result_value(self, valeur: str | None, dialect) -> str | None:  # type: ignore[override]
        return FieldEncryption.decrypt(valeur) if valeur else None


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class PatientEncounterModel(BaseModel):
    # Table BD : consultations
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_rendez_vous: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("rendez_vous.id", ondelete="SET NULL"),
        nullable=True, unique=True)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False)
    id_patient: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="RESTRICT"), nullable=False)
    motif_principal: Mapped[str | None] = mapped_column(Text, nullable=True)
    date_consultation: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow)
    date_suivi: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes_suivi: Mapped[str | None] = mapped_column(Text, nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum("open", "closed", name="encounter_status_enum"),
        nullable=False, default="open")


class EncounterMedicalReportModel(Base):
    # Table BD : rapports_médicaux
    __tablename__ = "rapports_medicaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_consultation: Mapped[int] = mapped_column(
        Integer, ForeignKey("consultations.id", ondelete="CASCADE"),
        nullable=False, unique=True)
    symptomes: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    diagnostic: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    traitement: Mapped[str | None] = mapped_column(EncryptedText, nullable=True)
    tension_arterielle: Mapped[str | None] = mapped_column(String(20), nullable=True)
    temperature: Mapped[str | None] = mapped_column(String(10), nullable=True)
    poids: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes_complementaires: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class EncounterPrescriptionModel(BaseModel):
    # Table BD : ordonnances
    __tablename__ = "ordonnances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_consultation: Mapped[int] = mapped_column(
        Integer, ForeignKey("consultations.id", ondelete="CASCADE"), nullable=False)
    nom_medicament: Mapped[str] = mapped_column(String(255), nullable=False)
    posologie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequence: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duree_jours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_chronique: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class AppointmentBodyChartModel(BaseModel):
    # Table BD : schémas_corporels_rdv
    __tablename__ = "schemas_corporels_rdv"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_rendez_vous: Mapped[int] = mapped_column(
        Integer, ForeignKey("rendez_vous.id", ondelete="CASCADE"), nullable=False)
    url_image: Mapped[str] = mapped_column(String(500), nullable=False)
    annotations: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
