"""Modèles SQLAlchemy du module FAQ — table compatible Laravel."""
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class FAQModel(BaseModel):
    __tablename__ = "faq"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    reponse: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
