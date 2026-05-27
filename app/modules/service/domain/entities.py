"""Entités domaine Service — aucune dépendance externe (pur Python)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal


@dataclass
class ServiceCategory:
    id: int
    name: str
    slug: str
    image: str | None
    description: str | None
    is_active: bool
    sort_order: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"ServiceCategory({self.id}: {self.name})"


@dataclass
class ServiceGallery:
    id: int
    service_id: int
    image: str
    caption: str | None
    sort_order: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServicePackage:
    id: int
    service_id: int
    name: str
    description: str | None
    price: Decimal
    sessions_count: int
    validity_days: int
    is_active: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def validity_end_date(self) -> date:
        """Retourne la date de fin de validité depuis created_at + validity_days."""
        return date(
            self.created_at.year,
            self.created_at.month,
            self.created_at.day,
        ).__class__.fromordinal(
            self.created_at.toordinal() + self.validity_days
        )


@dataclass
class ServiceEmployee:
    id: int
    service_id: int
    user_id: int
    is_primary: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceReview:
    id: int
    service_id: int
    user_id: int
    rating: int          # 1–5
    comment: str | None
    is_approved: bool
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError(f"rating must be between 1 and 5, got {self.rating}")


@dataclass
class Service:
    id: int
    vendor_id: int
    category_id: int | None
    name: str
    slug: str
    description: str | None
    short_description: str | None
    price: Decimal
    discount_price: Decimal | None
    duration_minutes: int
    is_active: bool
    is_featured: bool
    is_home_service: bool
    max_members: int
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Relations dénormalisées (chargées à la demande)
    category: ServiceCategory | None = field(default=None, compare=False)
    galleries: list[ServiceGallery] = field(default_factory=list, compare=False)
    packages: list[ServicePackage] = field(default_factory=list, compare=False)
    employees: list[ServiceEmployee] = field(default_factory=list, compare=False)
    average_rating: float | None = field(default=None, compare=False)
    review_count: int = field(default=0, compare=False)

    @property
    def effective_price(self) -> Decimal:
        """Prix effectif : discount_price si défini, sinon price."""
        return self.discount_price if self.discount_price is not None else self.price

    @property
    def is_discounted(self) -> bool:
        """True si un prix remisé est défini."""
        return self.discount_price is not None

    @property
    def rating_display(self) -> str:
        """Affichage du rating moyen ou 'Pas encore noté'."""
        if self.average_rating is None:
            return "Pas encore noté"
        return f"{self.average_rating:.1f}/5"

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def toggle_active(self) -> None:
        self.is_active = not self.is_active

    def __str__(self) -> str:
        return f"Service({self.id}: {self.name})"
