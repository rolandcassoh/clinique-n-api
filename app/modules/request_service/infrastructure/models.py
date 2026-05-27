"""Modèles SQLAlchemy du module RequestService — table compatible Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import DECIMAL, Date, Enum, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.request_service.domain.entities import RequestServiceStatus
from app.shared.models.base import BaseModel


class RequestServiceModel(BaseModel):
    __tablename__ = "request_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("service_categories.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 8), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 8), nullable=True)
    budget_min: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    preferred_date: Mapped[object | None] = mapped_column(Date, nullable=True)
    preferred_time: Mapped[object | None] = mapped_column(Time, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum(
            "pending", "in_review", "matched", "completed", "cancelled",
            name="request_service_status",
        ),
        default="pending",
        nullable=False,
    )
