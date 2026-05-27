"""Modèles SQLAlchemy du module world — noms de tables compatibles Laravel."""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel


class CountryModel(BaseModel):
    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    iso2: Mapped[str] = mapped_column(String(2), nullable=False)
    iso3: Mapped[str] = mapped_column(String(3), nullable=False)
    phone_code: Mapped[str] = mapped_column(String(20), nullable=False, default="")
    capital: Mapped[str | None] = mapped_column(String(100), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)

    states: Mapped[list["StateModel"]] = relationship(
        "StateModel", back_populates="country", lazy="select"
    )


class StateModel(BaseModel):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("countries.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(10), nullable=False, default="")

    country: Mapped["CountryModel"] = relationship(
        "CountryModel", back_populates="states", lazy="select"
    )
    cities: Mapped[list["CityModel"]] = relationship(
        "CityModel", back_populates="state", lazy="select"
    )


class CityModel(BaseModel):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("states.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    state: Mapped["StateModel"] = relationship(
        "StateModel", back_populates="cities", lazy="select"
    )
