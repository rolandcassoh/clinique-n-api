"""Modèles SQLAlchemy du module blog — tables compatibles Laravel."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class BlogCategoryModel(BaseModel):
    __tablename__ = "blog_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    posts: Mapped[list["BlogPostModel"]] = relationship(
        "BlogPostModel", back_populates="category", lazy="select"
    )


class BlogPostModel(BaseModel):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("blog_categories.id"), nullable=True
    )
    thumbnail: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    category: Mapped["BlogCategoryModel | None"] = relationship(
        "BlogCategoryModel", back_populates="posts", lazy="select"
    )
    # Relation vers l'auteur : pas de backref pour éviter une dépendance circulaire
    # On joint manuellement via une requête SQL dans le repository
