"""Modèles SQLAlchemy du module Logistic — tables compatibles Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class ShippingZoneModel(BaseModel):
    __tablename__ = "zones_livraison"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rates: Mapped[list[ShippingRateModel]] = relationship(back_populates="zone")


class ShippingRateModel(BaseModel):
    __tablename__ = "shipping_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_zone: Mapped[int] = mapped_column(Integer, ForeignKey("zones_livraison.id"), nullable=False)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    poids_min: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=0, nullable=False)
    poids_max: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    montant_min_commande: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    tarif: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    livraison_gratuite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    jours_livraison_min: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    jours_livraison_max: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    zone: Mapped[ShippingZoneModel] = relationship(back_populates="rates")
