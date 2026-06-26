"""Modèles SQLAlchemy — module constantes vitales."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class VitalSignsModel(BaseModel):
    # Table BD : signes_vitaux
    __tablename__ = "signes_vitaux"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_patient: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    enregistre_par: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="SET NULL"), nullable=True)
    id_rendez_vous: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tension_systolique: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tension_diastolique: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequence_cardiaque: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Decimal | None] = mapped_column(DECIMAL(4, 1), nullable=True)
    poids: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    taille: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2), nullable=True)
    saturation_oxygene: Mapped[int | None] = mapped_column(Integer, nullable=True)
    glycemie: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    enregistre_le: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)
