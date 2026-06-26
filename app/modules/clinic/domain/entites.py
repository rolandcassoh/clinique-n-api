"""Entités du domaine — module clinique. Aucun import FastAPI/SQLAlchemy."""
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional


# ── Clinique ──────────────────────────────────────────────────────────────────

@dataclass
class ClinicCategory:
    id: int
    nom: str
    identifiant_url: str
    image: Optional[str]
    description: Optional[str]
    est_actif: bool
    ordre_affichage: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


@dataclass
class Clinic:
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
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def toggle_active(self) -> None:
        self.est_actif = not self.est_actif


@dataclass
class ClinicService:
    id: int
    id_clinique: int
    nom: str
    description: Optional[str]
    prix: Decimal
    duree_minutes: int
    est_actif: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


# ── Médecin ───────────────────────────────────────────────────────────────────

@dataclass
class TimeSlot:
    start: datetime
    end: datetime

    def overlaps(self, other: "TimeSlot") -> bool:
        return self.start < other.end and self.end > other.start


@dataclass
class DoctorSession:
    id: int
    id_medecin: int
    jour_semaine: int  # 0=Lundi, 6=Dimanche (inchangé — contrat DB)
    heure_debut: time
    heure_fin: time
    duree_creneau_minutes: int
    max_patients_par_creneau: int
    est_actif: bool
    created_at: datetime
    updated_at: datetime

    def generate_theoretical_slots(self, for_date: date) -> list[datetime]:
        """Génère tous les créneaux théoriques pour une date donnée."""
        creneaux = []
        debut_creneau = datetime.combine(for_date, self.heure_debut)
        fin_limite = datetime.combine(for_date, self.heure_fin)
        delta = timedelta(minutes=self.duree_creneau_minutes)
        while debut_creneau + delta <= fin_limite:
            creneaux.append(debut_creneau)
            debut_creneau += delta
        return creneaux


@dataclass
class DoctorLeave:
    id: int
    id_medecin: int
    date_absence: date
    motif: Optional[str]
    journee_complete: bool
    heure_debut: Optional[time]
    heure_fin: Optional[time]
    created_at: datetime
    updated_at: datetime


@dataclass
class DoctorRating:
    id: int
    id_medecin: int
    id_utilisateur: int
    id_rendez_vous: Optional[int]
    note: int  # 1-5 (note de 1 à 5)
    commentaire: Optional[str]
    est_approuve: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def validate(self) -> None:
        if not (1 <= self.note <= 5):
            raise ValueError(f"La note doit être comprise entre 1 et 5, valeur reçue : {self.note}")


@dataclass
class Doctor:
    id: int
    id_utilisateur: int
    id_clinique: int
    specialite: Optional[str]
    qualification: Optional[str]
    annees_experience: int
    honoraires_consultation: Decimal
    montant_avance: Decimal
    est_disponible: bool
    id_agenda_google: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    # Enrichissement optionnel (chargé à la demande)
    note_moyenne: Optional[float] = None
    sessions: list[DoctorSession] = field(default_factory=list)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def toggle_availability(self) -> None:
        self.est_disponible = not self.est_disponible


@dataclass
class Receptionist:
    id: int
    id_utilisateur: int
    id_clinique: int
    est_actif: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
