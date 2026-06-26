"""Modèle SQLAlchemy du module slider — table compatible Laravel."""
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class SliderModel(BaseModel):
    __tablename__ = "diaporamas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    sous_titre: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    lien: Mapped[str | None] = mapped_column(String(500), nullable=True)
    texte_bouton: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    est_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
