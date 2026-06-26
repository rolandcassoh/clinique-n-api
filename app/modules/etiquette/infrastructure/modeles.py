"""Modèle SQLAlchemy du module tag — table compatible Laravel."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class TagModel(BaseModel):
    __tablename__ = "etiquettes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    type: Mapped[str | None] = mapped_column(String(50), nullable=True)
