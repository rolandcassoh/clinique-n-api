from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.shared.models.base import BaseModel


class PromotionModel(BaseModel):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("percentage", "fixed", name="promotion_type_enum"), nullable=False
    )
    valeur: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    montant_min_commande: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    remise_maximale: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    limite_utilisation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compteur_utilisation: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    debut_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expire_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    applicable_a: Mapped[str] = mapped_column(
        Enum("all", "products", "services", "appointments", name="promotion_applicable_enum"),
        default="all",
        nullable=False)


class PromotionUseModel(Base):
    __tablename__ = "promotion_uses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_promotion: Mapped[int] = mapped_column(
        Integer, ForeignKey("promotions.id", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    id_commande: Mapped[int | None] = mapped_column(Integer, nullable=True)
    id_rendez_vous: Mapped[int | None] = mapped_column(Integer, nullable=True)
    montant_remise: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    utilise_le: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
