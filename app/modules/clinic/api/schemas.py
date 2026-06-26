"""Schémas Pydantic v2 — module clinique."""
from datetime import date, datetime, time
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Catégorie de clinique ─────────────────────────────────────────────────────

class ClinicCategorySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    identifiant_url: str
    image: Optional[str]
    description: Optional[str]
    est_actif: bool
    ordre_affichage: int
    created_at: datetime


class ClinicCategoryCreateSchema(BaseModel):
    nom: str
    identifiant_url: str
    image: Optional[str] = None
    description: Optional[str] = None


class ClinicCategoryUpdateSchema(BaseModel):
    nom: Optional[str] = None
    identifiant_url: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    est_actif: Optional[bool] = None
    ordre_affichage: Optional[int] = None


# ── Clinique ──────────────────────────────────────────────────────────────────

class ClinicSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_proprietaire: int
    nom: str
    identifiant_url: str
    description: Optional[str]
    adresse: Optional[str]
    id_ville: Optional[int]
    telephone: Optional[str]
    courriel: Optional[str]
    site_web: Optional[str]
    logo: Optional[str]
    image_couverture: Optional[str]
    est_actif: bool
    est_mis_en_avant: bool
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    taux_commission: Decimal
    created_at: datetime
    updated_at: datetime


class ClinicCreateSchema(BaseModel):
    id_proprietaire: int
    nom: str
    identifiant_url: str
    description: Optional[str] = None
    adresse: Optional[str] = None
    id_ville: Optional[int] = None
    telephone: Optional[str] = None
    courriel: Optional[str] = None
    site_web: Optional[str] = None
    logo: Optional[str] = None
    image_couverture: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    taux_commission: Decimal = Decimal("0")


class ClinicUpdateSchema(BaseModel):
    nom: Optional[str] = None
    identifiant_url: Optional[str] = None
    description: Optional[str] = None
    adresse: Optional[str] = None
    id_ville: Optional[int] = None
    telephone: Optional[str] = None
    courriel: Optional[str] = None
    site_web: Optional[str] = None
    logo: Optional[str] = None
    image_couverture: Optional[str] = None
    est_actif: Optional[bool] = None
    est_mis_en_avant: Optional[bool] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    taux_commission: Optional[Decimal] = None


# ── Service de clinique ───────────────────────────────────────────────────────

class ClinicServiceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_clinique: int
    nom: str
    description: Optional[str]
    prix: Decimal
    duree_minutes: int
    est_actif: bool
    created_at: datetime


class ClinicServiceCreateSchema(BaseModel):
    nom: str
    description: Optional[str] = None
    prix: Decimal = Decimal("0")
    duree_minutes: int = 30


class ClinicServiceUpdateSchema(BaseModel):
    nom: Optional[str] = None
    description: Optional[str] = None
    prix: Optional[Decimal] = None
    duree_minutes: Optional[int] = None
    est_actif: Optional[bool] = None


# ── Médecin ───────────────────────────────────────────────────────────────────

class DoctorSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    id_clinique: int
    specialite: Optional[str]
    qualification: Optional[str]
    annees_experience: int
    honoraires_consultation: Decimal
    montant_avance: Decimal
    est_disponible: bool
    note_moyenne: Optional[float]
    created_at: datetime
    updated_at: datetime


class DoctorCreateSchema(BaseModel):
    id_utilisateur: int
    specialite: Optional[str] = None
    qualification: Optional[str] = None
    annees_experience: int = 0
    honoraires_consultation: Decimal = Decimal("0")
    montant_avance: Decimal = Decimal("0")


class DoctorUpdateSchema(BaseModel):
    specialite: Optional[str] = None
    qualification: Optional[str] = None
    annees_experience: Optional[int] = None
    honoraires_consultation: Optional[Decimal] = None
    montant_avance: Optional[Decimal] = None
    est_disponible: Optional[bool] = None


class DoctorAvailabilitySchema(BaseModel):
    est_disponible: bool


# ── Session médecin ───────────────────────────────────────────────────────────

class DoctorSessionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_medecin: int
    jour_semaine: int
    heure_debut: time
    heure_fin: time
    duree_creneau_minutes: int
    max_patients_par_creneau: int
    est_actif: bool
    created_at: datetime


class DoctorSessionCreateSchema(BaseModel):
    jour_semaine: int = Field(..., ge=0, le=6)
    heure_debut: time
    heure_fin: time
    duree_creneau_minutes: int = 30
    max_patients_par_creneau: int = 1


class DoctorSessionUpdateSchema(BaseModel):
    jour_semaine: Optional[int] = Field(None, ge=0, le=6)
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    duree_creneau_minutes: Optional[int] = None
    max_patients_par_creneau: Optional[int] = None
    est_actif: Optional[bool] = None


# ── Congé médecin ─────────────────────────────────────────────────────────────

class DoctorLeaveSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_medecin: int
    date_absence: date
    motif: Optional[str]
    journee_complete: bool
    heure_debut: Optional[time]
    heure_fin: Optional[time]
    created_at: datetime


class DoctorLeaveCreateSchema(BaseModel):
    date_absence: date
    motif: Optional[str] = None
    journee_complete: bool = True
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None


# ── Note médecin ──────────────────────────────────────────────────────────────

class DoctorRatingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_medecin: int
    id_utilisateur: int
    id_rendez_vous: Optional[int]
    note: int
    commentaire: Optional[str]
    est_approuve: bool
    created_at: datetime


class DoctorRatingCreateSchema(BaseModel):
    note: int = Field(..., ge=1, le=5)
    commentaire: Optional[str] = None
    id_rendez_vous: Optional[int] = None


# ── Réceptionniste ────────────────────────────────────────────────────────────

class ReceptionistSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    id_clinique: int
    est_actif: bool
    created_at: datetime


class ReceptionistCreateSchema(BaseModel):
    id_utilisateur: int


# ── Créneaux disponibles ──────────────────────────────────────────────────────

class AvailableSlotsSchema(BaseModel):
    id_medecin: int
    date: date
    slots: list[datetime]
