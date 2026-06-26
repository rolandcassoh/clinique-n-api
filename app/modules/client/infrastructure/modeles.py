from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class OtherPatientModel(BaseModel):
    """Membres de famille d'un patient — table other_patients (compatible Laravel).

    Représente les autres patients liés à un utilisateur principal.
    """

    __tablename__ = "autres_patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    relation: Mapped[str] = mapped_column(String(100), nullable=False)
    date_naissance: Mapped[date | None] = mapped_column(Date, nullable=True)
    sexe: Mapped[str | None] = mapped_column(
        Enum("male", "female", "other", name="other_patient_gender_enum"), nullable=True)
    groupe_sanguin: Mapped[str | None] = mapped_column(String(5), nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
