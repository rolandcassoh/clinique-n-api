"""Entités domaine Service — aucune dépendance externe (pur Python)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class ServiceCategory:
    id: int
    nom: str
    identifiant_url: str
    image: str | None
    description: str | None
    est_actif: bool
    ordre_affichage: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"ServiceCategory({self.id}: {self.nom})"


@dataclass
class ServiceGallery:
    id: int
    id_service: int
    image: str
    legende: str | None
    ordre_affichage: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServicePackage:
    id: int
    id_service: int
    nom: str
    description: str | None
    prix: Decimal
    nombre_seances: int
    jours_validite: int
    est_actif: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def validity_end_date(self) -> date:
        """Retourne la date de fin de validité depuis created_at + jours_validite."""
        return date(
            self.created_at.year,
            self.created_at.month,
            self.created_at.day,
        ).__class__.fromordinal(
            self.created_at.toordinal() + self.jours_validite
        )


@dataclass
class ServiceEmployee:
    id: int
    id_service: int
    id_utilisateur: int
    est_principal: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceReview:
    id: int
    id_service: int
    id_utilisateur: int
    note: int          # 1–5
    commentaire: str | None
    est_approuve: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 1 <= self.note <= 5:
            raise ValueError(f"La note doit être comprise entre 1 et 5, valeur reçue : {self.note}")


@dataclass
class Service:
    id: int
    id_prestataire: int
    id_categorie: int | None
    nom: str
    identifiant_url: str
    description: str | None
    short_description: str | None
    prix: Decimal
    prix_remise: Decimal | None
    duree_minutes: int
    est_actif: bool
    est_mis_en_avant: bool
    service_domicile: bool
    max_membres: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Relations dénormalisées (chargées à la demande)
    category: ServiceCategory | None = field(default=None, compare=False)
    galleries: list[ServiceGallery] = field(default_factory=list, compare=False)
    packages: list[ServicePackage] = field(default_factory=list, compare=False)
    employees: list[ServiceEmployee] = field(default_factory=list, compare=False)
    note_moyenne: float | None = field(default=None, compare=False)
    review_count: int = field(default=0, compare=False)

    @property
    def effective_price(self) -> Decimal:
        """Prix effectif : prix_remise si défini, sinon prix."""
        return self.prix_remise if self.prix_remise is not None else self.prix

    @property
    def is_discounted(self) -> bool:
        """True si un prix remisé est défini."""
        return self.prix_remise is not None

    @property
    def rating_display(self) -> str:
        """Affichage du note moyen ou 'Pas encore noté'."""
        if self.note_moyenne is None:
            return "Pas encore noté"
        return f"{self.note_moyenne:.1f}/5"

    def deactivate(self) -> None:
        self.est_actif = False

    def activate(self) -> None:
        self.est_actif = True

    def toggle_active(self) -> None:
        self.est_actif = not self.est_actif

    def __str__(self) -> str:
        return f"Service({self.id}: {self.nom})"
