"""Modèle SQLAlchemy du module langue — table compatible Laravel."""
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class LanguageModel(BaseModel):
    __tablename__ = "langues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    nom_natif: Mapped[str | None] = mapped_column(String(100), nullable=True)
    drapeau: Mapped[str | None] = mapped_column(String(500), nullable=True)
    est_defaut: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    sens_ecriture: Mapped[str] = mapped_column(
        Enum("ltr", "rtl", name="language_direction"), nullable=False, default="ltr")
