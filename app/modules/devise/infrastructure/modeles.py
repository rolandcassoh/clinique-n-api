"""Modèle SQLAlchemy du module devise — table compatible Laravel."""
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class CurrencyModel(BaseModel):
    __tablename__ = "devises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    symbole: Mapped[str] = mapped_column(String(10), nullable=False)
    taux_change: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False, default=Decimal("1"))
    est_defaut: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
