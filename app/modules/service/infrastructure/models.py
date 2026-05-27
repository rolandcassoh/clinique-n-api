"""Modèles SQLAlchemy du module Service — tables compatibles Laravel."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DECIMAL,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class ServiceCategoryModel(BaseModel):
    __tablename__ = "service_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    services: Mapped[list[ServiceModel]] = relationship(back_populates="category")


class ServiceModel(BaseModel):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("service_categories.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    discount_price: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_home_service: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_members: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    category: Mapped[ServiceCategoryModel | None] = relationship(back_populates="services")
    packages: Mapped[list[ServicePackageModel]] = relationship(back_populates="service")
    employees: Mapped[list[ServiceEmployeeModel]] = relationship(back_populates="service")
    galleries: Mapped[list[ServiceGalleryModel]] = relationship(
        back_populates="service", order_by="ServiceGalleryModel.sort_order"
    )
    reviews: Mapped[list[ServiceReviewModel]] = relationship(back_populates="service")


class ServicePackageModel(BaseModel):
    __tablename__ = "service_packages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    sessions_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    validity_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="packages")


class ServiceEmployeeModel(BaseModel):
    __tablename__ = "service_employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="employees")


class ServiceGalleryModel(BaseModel):
    __tablename__ = "service_galleries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    image: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="galleries")


class ServiceReviewModel(BaseModel):
    __tablename__ = "service_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_id: Mapped[int] = mapped_column(Integer, ForeignKey("services.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    service: Mapped[ServiceModel] = relationship(back_populates="reviews")
