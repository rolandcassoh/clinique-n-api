"""Modèles SQLAlchemy du module RequestService — table compatible Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import DECIMAL, Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.demande_service.domain.entites import RequestServiceStatus
from app.shared.models.base import BaseModel


class RequestServiceModel(BaseModel):
    __tablename__ = "request_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_categorie: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories_services.id"), nullable=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    localisation: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 8), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 8), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    preferred_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    creneau_prefere: Mapped[object | None] = mapped_column(Time, nullable=True)
    statut: Mapped[str] = mapped_column(
        Enum(
            "pending", "in_review", "matched", "completed", "cancelled",
            name="request_service_status",
        ),
        default="pending",
        nullable=False)
