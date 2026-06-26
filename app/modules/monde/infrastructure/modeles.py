"""Modèles SQLAlchemy du module world — noms de tables compatibles Laravel."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class CountryModel(BaseModel):
    __tablename__ = "pays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    code_iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    code_iso3: Mapped[str] = mapped_column(String(3), nullable=False)
    indicatif_telephone: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    capitale: Mapped[str | None] = mapped_column(String(100), nullable=True)
    devise: Mapped[str | None] = mapped_column(String(10), nullable=True)

    states: Mapped[list["StateModel"]] = relationship(
        "StateModel", back_populates="country", lazy="select"
    )


class StateModel(BaseModel):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_pays: Mapped[int] = mapped_column(
        Integer, ForeignKey("pays.id"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    code_region: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    country: Mapped["CountryModel"] = relationship(
        "CountryModel", back_populates="states", lazy="select"
    )
    cities: Mapped[list["CityModel"]] = relationship(
        "CityModel", back_populates="state", lazy="select"
    )


class CityModel(BaseModel):
    __tablename__ = "villes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_region: Mapped[int] = mapped_column(
        Integer, ForeignKey("regions.id"), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)

    state: Mapped["StateModel"] = relationship(
        "StateModel", back_populates="cities", lazy="select"
    )
