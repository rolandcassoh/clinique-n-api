"""Interfaces (ABC) des repositories Service."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.service.domain.entites import (
    Service,
    ServiceCategory,
    ServiceEmployee,
    ServiceGallery,
    ServicePackage,
    ServiceReview,
)
from app.shared.schemas.pagination import PaginationParams


class ServiceCategoryRepository(ABC):
    @abstractmethod
    async def list_active(self, params: PaginationParams) -> tuple[list[ServiceCategory], int]: ...

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> ServiceCategory | None: ...

    @abstractmethod
    async def get_by_id(self, id_categorie: int) -> ServiceCategory | None: ...

    @abstractmethod
    async def create(
        self,
        nom: str,
        identifiant_url: str,
        image: str | None,
        description: str | None,
        est_actif: bool,
        ordre_affichage: int,
    ) -> ServiceCategory: ...

    @abstractmethod
    async def update(
        self,
        id_categorie: int,
        nom: str | None,
        identifiant_url: str | None,
        image: str | None,
        description: str | None,
        est_actif: bool | None,
        ordre_affichage: int | None,
    ) -> ServiceCategory | None: ...

    @abstractmethod
    async def soft_delete(self, id_categorie: int) -> bool: ...

    @abstractmethod
    async def slug_exists(self, identifiant_url: str, exclude_id: int | None = None) -> bool: ...


class ServiceRepository(ABC):
    @abstractmethod
    async def list_public(
        self,
        params: PaginationParams,
        id_categorie: int | None = None,
        search: str | None = None,
        service_domicile: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> tuple[list[Service], int]: ...

    @abstractmethod
    async def get_by_slug(self, identifiant_url: str) -> Service | None: ...

    @abstractmethod
    async def get_by_id(self, id_service: int) -> Service | None: ...

    @abstractmethod
    async def create(
        self,
        id_prestataire: int,
        id_categorie: int | None,
        nom: str,
        identifiant_url: str,
        description: str | None,
        short_description: str | None,
        prix: Decimal,
        prix_remise: Decimal | None,
        duree_minutes: int,
        est_actif: bool,
        est_mis_en_avant: bool,
        service_domicile: bool,
        max_membres: int,
    ) -> Service: ...

    @abstractmethod
    async def update(
        self,
        id_service: int,
        id_prestataire: int | None,
        id_categorie: int | None,
        nom: str | None,
        identifiant_url: str | None,
        description: str | None,
        short_description: str | None,
        prix: Decimal | None,
        prix_remise: Decimal | None,
        duree_minutes: int | None,
        est_actif: bool | None,
        est_mis_en_avant: bool | None,
        service_domicile: bool | None,
        max_membres: int | None,
    ) -> Service | None: ...

    @abstractmethod
    async def soft_delete(self, id_service: int) -> bool: ...

    @abstractmethod
    async def slug_exists(self, identifiant_url: str, exclude_id: int | None = None) -> bool: ...

    @abstractmethod
    async def get_average_rating(self, id_service: int) -> float | None: ...


class ServicePackageRepository(ABC):
    @abstractmethod
    async def list_by_service(self, id_service: int) -> list[ServicePackage]: ...

    @abstractmethod
    async def get_by_id(self, package_id: int) -> ServicePackage | None: ...

    @abstractmethod
    async def create(
        self,
        id_service: int,
        nom: str,
        description: str | None,
        prix: Decimal,
        nombre_seances: int,
        jours_validite: int,
        est_actif: bool,
    ) -> ServicePackage: ...

    @abstractmethod
    async def update(
        self,
        package_id: int,
        nom: str | None,
        description: str | None,
        prix: Decimal | None,
        nombre_seances: int | None,
        jours_validite: int | None,
        est_actif: bool | None,
    ) -> ServicePackage | None: ...

    @abstractmethod
    async def delete(self, package_id: int) -> bool: ...


class ServiceEmployeeRepository(ABC):
    @abstractmethod
    async def list_by_service(self, id_service: int) -> list[ServiceEmployee]: ...

    @abstractmethod
    async def get_by_id(self, employee_id: int) -> ServiceEmployee | None: ...

    @abstractmethod
    async def assign(self, id_service: int, id_utilisateur: int, est_principal: bool) -> ServiceEmployee: ...

    @abstractmethod
    async def remove(self, employee_id: int) -> bool: ...


class ServiceGalleryRepository(ABC):
    @abstractmethod
    async def list_by_service(self, id_service: int) -> list[ServiceGallery]: ...

    @abstractmethod
    async def get_by_id(self, gallery_id: int) -> ServiceGallery | None: ...

    @abstractmethod
    async def add_image(
        self,
        id_service: int,
        image: str,
        legende: str | None,
        ordre_affichage: int,
    ) -> ServiceGallery: ...

    @abstractmethod
    async def delete(self, gallery_id: int) -> bool: ...

    @abstractmethod
    async def reorder(self, items: list[dict]) -> None: ...


class ServiceReviewRepository(ABC):
    @abstractmethod
    async def list_approved(
        self, id_service: int, params: PaginationParams
    ) -> tuple[list[ServiceReview], int]: ...

    @abstractmethod
    async def user_has_review(self, id_service: int, id_utilisateur: int) -> bool: ...

    @abstractmethod
    async def create(
        self,
        id_service: int,
        id_utilisateur: int,
        note: int,
        commentaire: str | None,
    ) -> ServiceReview: ...
