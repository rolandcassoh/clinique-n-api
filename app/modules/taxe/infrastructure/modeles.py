"""Modèle SQLAlchemy du module tax."""
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class TaxModel(BaseModel):
    __tablename__ = "taxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    tarif: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    type: Mapped[str] = mapped_column(
        Enum("percentage", "fixed", name="tax_type_enum"),
        default="percentage",
        nullable=False,
    )
    id_pays: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("pays.id", ondelete="SET NULL"), nullable=True)
    est_defaut: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
