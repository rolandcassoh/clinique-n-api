"""Modèles SQLAlchemy du module blog — tables compatibles Laravel."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class BlogCategoryModel(BaseModel):
    __tablename__ = "blog_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    posts: Mapped[list["BlogPostModel"]] = relationship(
        "BlogPostModel", back_populates="category", lazy="select"
    )


class BlogPostModel(BaseModel):
    __tablename__ = "articles_blog"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    extrait: Mapped[str | None] = mapped_column(Text, nullable=True)
    contenu: Mapped[str] = mapped_column(Text, nullable=False)
    id_auteur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id"), nullable=False)
    id_categorie: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("blog_categories.id"), nullable=True)
    miniature: Mapped[str | None] = mapped_column(String(500), nullable=True)
    est_publie: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    publie_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    vues: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped["BlogCategoryModel | None"] = relationship(
        "BlogCategoryModel", back_populates="posts", lazy="select"
    )
    # Relation vers l'auteur : pas de backref pour éviter une dépendance circulaire
    # On joint manuellement via une requête SQL dans le repository
