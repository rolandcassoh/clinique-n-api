"""Modèles SQLAlchemy — module clinique. Tables compatibles Laravel."""
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models.base import BaseModel


class ClinicCategoryModel(BaseModel):
    # Table BD : catégories_cliniques
    __tablename__ = "categories_cliniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    image: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    ordre_affichage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ClinicModel(BaseModel):
    # Table BD : cliniques
    __tablename__ = "cliniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_proprietaire: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    identifiant_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    adresse: Mapped[str | None] = mapped_column(String(500), nullable=True)
    id_ville: Mapped[int | None] = mapped_column(Integer, nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    courriel: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_web: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_couverture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    est_mis_en_avant: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 8), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(DECIMAL(11, 8), nullable=True)
    taux_commission: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), default=0, nullable=False)


class ClinicServiceModel(BaseModel):
    # Table BD : services_cliniques
    __tablename__ = "services_cliniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="CASCADE"), nullable=False, index=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    prix: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    duree_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DoctorModel(BaseModel):
    # Table BD : médecins
    __tablename__ = "medecins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), unique=True, nullable=False)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="CASCADE"), nullable=False, index=True)
    specialite: Mapped[str | None] = mapped_column(String(255), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(500), nullable=True)
    annees_experience: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    honoraires_consultation: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    montant_avance: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), default=0, nullable=False)
    est_disponible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    id_agenda_google: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DoctorSessionModel(BaseModel):
    # Table BD : sessions_médecin
    __tablename__ = "sessions_medecin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("medecins.id", ondelete="CASCADE"), nullable=False, index=True)
    jour_semaine: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    heure_debut: Mapped[time] = mapped_column(Time, nullable=False)
    heure_fin: Mapped[time] = mapped_column(Time, nullable=False)
    duree_creneau_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_patients_par_creneau: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DoctorLeaveModel(BaseModel):
    # Table BD : congés_médecin
    __tablename__ = "conges_medecin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("medecins.id", ondelete="CASCADE"), nullable=False, index=True)
    date_absence: Mapped[date] = mapped_column(Date, nullable=False)
    motif: Mapped[str | None] = mapped_column(String(255), nullable=True)
    journee_complete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    heure_debut: Mapped[time | None] = mapped_column(Time, nullable=True)
    heure_fin: Mapped[time | None] = mapped_column(Time, nullable=True)


class DoctorRatingModel(BaseModel):
    # Table BD : évaluations_médecin
    __tablename__ = "evaluations_medecin"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_medecin: Mapped[int] = mapped_column(
        Integer, ForeignKey("medecins.id", ondelete="CASCADE"), nullable=False, index=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False)
    id_rendez_vous: Mapped[int | None] = mapped_column(Integer, nullable=True)
    note: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    commentaire: Mapped[str | None] = mapped_column(Text, nullable=True)
    est_approuve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ReceptionistModel(BaseModel):
    # Table BD : réceptionnistes
    __tablename__ = "receptionnistes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), unique=True, nullable=False)
    id_clinique: Mapped[int] = mapped_column(
        Integer, ForeignKey("cliniques.id", ondelete="CASCADE"), nullable=False, index=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
