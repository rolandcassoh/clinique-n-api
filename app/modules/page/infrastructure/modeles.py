"""Modèles SQLAlchemy du module page — table compatible Laravel."""
from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class PageModel(BaseModel):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    titre_meta: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_publie: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
