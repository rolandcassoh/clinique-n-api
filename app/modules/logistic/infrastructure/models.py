"""Modèles SQLAlchemy du module Logistic — tables compatibles Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class ShippingZoneModel(BaseModel):
    __tablename__ = "shipping_zones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rates: Mapped[list[ShippingRateModel]] = relationship(back_populates="zone")


class ShippingRateModel(BaseModel):
    __tablename__ = "shipping_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("shipping_zones.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    min_weight: Mapped[Decimal] = mapped_column(DECIMAL(8, 2), default=0, nullable=False)
    max_weight: Mapped[Decimal | None] = mapped_column(DECIMAL(8, 2), nullable=True)
    min_order_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    rate: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    is_free_shipping: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    estimated_days_min: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    estimated_days_max: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    zone: Mapped[ShippingZoneModel] = relationship(back_populates="rates")
