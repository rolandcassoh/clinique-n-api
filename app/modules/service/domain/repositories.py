"""Interfaces (ABC) des repositories Service."""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal

from app.modules.service.domain.entities import (
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
    async def get_by_slug(self, slug: str) -> ServiceCategory | None: ...

    @abstractmethod
    async def get_by_id(self, category_id: int) -> ServiceCategory | None: ...

    @abstractmethod
    async def create(
        self,
        name: str,
        slug: str,
        image: str | None,
        description: str | None,
        is_active: bool,
        sort_order: int,
    ) -> ServiceCategory: ...

    @abstractmethod
    async def update(
        self,
        category_id: int,
        name: str | None,
        slug: str | None,
        image: str | None,
        description: str | None,
        is_active: bool | None,
        sort_order: int | None,
    ) -> ServiceCategory | None: ...

    @abstractmethod
    async def soft_delete(self, category_id: int) -> bool: ...

    @abstractmethod
    async def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool: ...


class ServiceRepository(ABC):
    @abstractmethod
    async def list_public(
        self,
        params: PaginationParams,
        category_id: int | None = None,
        search: str | None = None,
        is_home_service: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> tuple[list[Service], int]: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Service | None: ...

    @abstractmethod
    async def get_by_id(self, service_id: int) -> Service | None: ...

    @abstractmethod
    async def create(
        self,
        vendor_id: int,
        category_id: int | None,
        name: str,
        slug: str,
        description: str | None,
        short_description: str | None,
        price: Decimal,
        discount_price: Decimal | None,
        duration_minutes: int,
        is_active: bool,
        is_featured: bool,
        is_home_service: bool,
        max_members: int,
    ) -> Service: ...

    @abstractmethod
    async def update(
        self,
        service_id: int,
        vendor_id: int | None,
        category_id: int | None,
        name: str | None,
        slug: str | None,
        description: str | None,
        short_description: str | None,
        price: Decimal | None,
        discount_price: Decimal | None,
        duration_minutes: int | None,
        is_active: bool | None,
        is_featured: bool | None,
        is_home_service: bool | None,
        max_members: int | None,
    ) -> Service | None: ...

    @abstractmethod
    async def soft_delete(self, service_id: int) -> bool: ...

    @abstractmethod
    async def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool: ...

    @abstractmethod
    async def get_average_rating(self, service_id: int) -> float | None: ...


class ServicePackageRepository(ABC):
    @abstractmethod
    async def list_by_service(self, service_id: int) -> list[ServicePackage]: ...

    @abstractmethod
    async def get_by_id(self, package_id: int) -> ServicePackage | None: ...

    @abstractmethod
    async def create(
        self,
        service_id: int,
        name: str,
        description: str | None,
        price: Decimal,
        sessions_count: int,
        validity_days: int,
        is_active: bool,
    ) -> ServicePackage: ...

    @abstractmethod
    async def update(
        self,
        package_id: int,
        name: str | None,
        description: str | None,
        price: Decimal | None,
        sessions_count: int | None,
        validity_days: int | None,
        is_active: bool | None,
    ) -> ServicePackage | None: ...

    @abstractmethod
    async def delete(self, package_id: int) -> bool: ...


class ServiceEmployeeRepository(ABC):
    @abstractmethod
    async def list_by_service(self, service_id: int) -> list[ServiceEmployee]: ...

    @abstractmethod
    async def get_by_id(self, employee_id: int) -> ServiceEmployee | None: ...

    @abstractmethod
    async def assign(self, service_id: int, user_id: int, is_primary: bool) -> ServiceEmployee: ...

    @abstractmethod
    async def remove(self, employee_id: int) -> bool: ...


class ServiceGalleryRepository(ABC):
    @abstractmethod
    async def list_by_service(self, service_id: int) -> list[ServiceGallery]: ...

    @abstractmethod
    async def get_by_id(self, gallery_id: int) -> ServiceGallery | None: ...

    @abstractmethod
    async def add_image(
        self,
        service_id: int,
        image: str,
        caption: str | None,
        sort_order: int,
    ) -> ServiceGallery: ...

    @abstractmethod
    async def delete(self, gallery_id: int) -> bool: ...

    @abstractmethod
    async def reorder(self, items: list[dict]) -> None: ...


class ServiceReviewRepository(ABC):
    @abstractmethod
    async def list_approved(
        self, service_id: int, params: PaginationParams
    ) -> tuple[list[ServiceReview], int]: ...

    @abstractmethod
    async def user_has_review(self, service_id: int, user_id: int) -> bool: ...

    @abstractmethod
    async def create(
        self,
        service_id: int,
        user_id: int,
        rating: int,
        comment: str | None,
    ) -> ServiceReview: ...
