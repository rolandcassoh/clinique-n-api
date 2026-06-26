"""Modèles SQLAlchemy — module abonnements."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel
from app.database import Base


class SubscriptionPlanModel(BaseModel):
    # Table BD : plans_abonnement
    __tablename__ = "plans_abonnement"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prix: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    periode_facturation: Mapped[str] = mapped_column(
        Enum("monthly", "yearly", name="billing_period_enum"),
        default="monthly",
        nullable=False)
    jours_essai: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    est_mis_en_avant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PlanLimitationModel(Base):
    """Table plan_limitations — pas de soft delete."""
    # Table BD : limitations_plan
    __tablename__ = "plan_limitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_plan: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans_abonnement.id", ondelete="CASCADE"),
        nullable=False, index=True)
    fonctionnalite: Mapped[str] = mapped_column(String(100), nullable=False)
    valeur: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SubscriptionModel(BaseModel):
    # Table BD : abonnements
    __tablename__ = "abonnements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="CASCADE"), nullable=False, index=True)
    id_plan: Mapped[int] = mapped_column(
        Integer, ForeignKey("plans_abonnement.id"), nullable=False)
    statut: Mapped[str] = mapped_column(
        Enum("trial", "active", "cancelled", "expired", name="subscription_status_enum"),
        default="trial",
        nullable=False)
    debut_le: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fin_le: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    renouvellement_auto: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    annule_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
