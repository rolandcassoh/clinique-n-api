"""Use Cases du module Service."""
from __future__ import annotations

from decimal import Decimal

from app.modules.service.domain.entities import (
    Service,
    ServiceCategory,
    ServiceEmployee,
    ServiceGallery,
    ServicePackage,
    ServiceReview,
)
from app.modules.service.domain.exceptions import (
    CategorySlugConflictError,
    DuplicateReviewError,
    ServiceCategoryNotFoundError,
    ServiceEmployeeNotFoundError,
    ServiceGalleryNotFoundError,
    ServiceNotFoundError,
    ServicePackageNotFoundError,
    ServiceSlugConflictError,
)
from app.modules.service.domain.repositories import (
    ServiceCategoryRepository,
    ServiceEmployeeRepository,
    ServiceGalleryRepository,
    ServicePackageRepository,
    ServiceRepository,
    ServiceReviewRepository,
)
from app.shared.schemas.pagination import Page, PaginationParams


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class ListActiveCategoriesUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, params: PaginationParams) -> Page[ServiceCategory]:
        items, total = await self._repo.list_active(params)
        return Page.create(data=items, total=total, params=params)


class GetCategoryBySlugUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> ServiceCategory:
        cat = await self._repo.get_by_slug(slug)
        if cat is None:
            raise ServiceCategoryNotFoundError(slug)
        return cat


class CreateCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        name: str,
        slug: str,
        image: str | None = None,
        description: str | None = None,
        is_active: bool = True,
        sort_order: int = 0,
    ) -> ServiceCategory:
        if await self._repo.slug_exists(slug):
            raise CategorySlugConflictError(slug)
        return await self._repo.create(
            name=name, slug=slug, image=image, description=description,
            is_active=is_active, sort_order=sort_order,
        )


class UpdateCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        category_id: int,
        name: str | None = None,
        slug: str | None = None,
        image: str | None = None,
        description: str | None = None,
        is_active: bool | None = None,
        sort_order: int | None = None,
    ) -> ServiceCategory:
        if slug and await self._repo.slug_exists(slug, exclude_id=category_id):
            raise CategorySlugConflictError(slug)
        cat = await self._repo.update(
            category_id=category_id, name=name, slug=slug, image=image,
            description=description, is_active=is_active, sort_order=sort_order,
        )
        if cat is None:
            raise ServiceCategoryNotFoundError(category_id)
        return cat


class DeleteCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, category_id: int) -> None:
        deleted = await self._repo.soft_delete(category_id)
        if not deleted:
            raise ServiceCategoryNotFoundError(category_id)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

class ListServicesUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        category_id: int | None = None,
        search: str | None = None,
        is_home_service: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> Page[Service]:
        items, total = await self._repo.list_public(
            params=params,
            category_id=category_id,
            search=search,
            is_home_service=is_home_service,
            min_price=min_price,
            max_price=max_price,
        )
        return Page.create(data=items, total=total, params=params)


class GetServiceBySlugUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, slug: str) -> Service:
        service = await self._repo.get_by_slug(slug)
        if service is None:
            raise ServiceNotFoundError(slug)
        return service


class CreateServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        vendor_id: int,
        name: str,
        slug: str,
        price: Decimal,
        category_id: int | None = None,
        description: str | None = None,
        short_description: str | None = None,
        discount_price: Decimal | None = None,
        duration_minutes: int = 60,
        is_active: bool = True,
        is_featured: bool = False,
        is_home_service: bool = False,
        max_members: int = 1,
    ) -> Service:
        if await self._repo.slug_exists(slug):
            raise ServiceSlugConflictError(slug)
        return await self._repo.create(
            vendor_id=vendor_id, category_id=category_id, name=name, slug=slug,
            description=description, short_description=short_description,
            price=price, discount_price=discount_price, duration_minutes=duration_minutes,
            is_active=is_active, is_featured=is_featured, is_home_service=is_home_service,
            max_members=max_members,
        )


class UpdateServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        service_id: int,
        vendor_id: int | None = None,
        category_id: int | None = None,
        name: str | None = None,
        slug: str | None = None,
        description: str | None = None,
        short_description: str | None = None,
        price: Decimal | None = None,
        discount_price: Decimal | None = None,
        duration_minutes: int | None = None,
        is_active: bool | None = None,
        is_featured: bool | None = None,
        is_home_service: bool | None = None,
        max_members: int | None = None,
    ) -> Service:
        if slug and await self._repo.slug_exists(slug, exclude_id=service_id):
            raise ServiceSlugConflictError(slug)
        service = await self._repo.update(
            service_id=service_id, vendor_id=vendor_id, category_id=category_id,
            name=name, slug=slug, description=description, short_description=short_description,
            price=price, discount_price=discount_price, duration_minutes=duration_minutes,
            is_active=is_active, is_featured=is_featured, is_home_service=is_home_service,
            max_members=max_members,
        )
        if service is None:
            raise ServiceNotFoundError(service_id)
        return service


class DeleteServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int) -> None:
        deleted = await self._repo.soft_delete(service_id)
        if not deleted:
            raise ServiceNotFoundError(service_id)


class ToggleServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int) -> Service:
        service = await self._repo.get_by_id(service_id)
        if service is None:
            raise ServiceNotFoundError(service_id)
        updated = await self._repo.update(
            service_id=service_id, vendor_id=None, category_id=None, name=None,
            slug=None, description=None, short_description=None, price=None,
            discount_price=None, duration_minutes=None, is_active=not service.is_active,
            is_featured=None, is_home_service=None, max_members=None,
        )
        if updated is None:
            raise ServiceNotFoundError(service_id)
        return updated


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class ListPackagesUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int) -> list[ServicePackage]:
        return await self._repo.list_by_service(service_id)


class CreatePackageUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        service_id: int,
        name: str,
        price: Decimal,
        sessions_count: int = 1,
        validity_days: int = 30,
        description: str | None = None,
        is_active: bool = True,
    ) -> ServicePackage:
        return await self._repo.create(
            service_id=service_id, name=name, description=description,
            price=price, sessions_count=sessions_count, validity_days=validity_days,
            is_active=is_active,
        )


class UpdatePackageUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        package_id: int,
        name: str | None = None,
        description: str | None = None,
        price: Decimal | None = None,
        sessions_count: int | None = None,
        validity_days: int | None = None,
        is_active: bool | None = None,
    ) -> ServicePackage:
        pkg = await self._repo.update(
            package_id=package_id, name=name, description=description,
            price=price, sessions_count=sessions_count, validity_days=validity_days,
            is_active=is_active,
        )
        if pkg is None:
            raise ServicePackageNotFoundError(package_id)
        return pkg


class DeletePackageUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(self, package_id: int) -> None:
        deleted = await self._repo.delete(package_id)
        if not deleted:
            raise ServicePackageNotFoundError(package_id)


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

class AssignEmployeeUseCase:
    def __init__(self, repo: ServiceEmployeeRepository) -> None:
        self._repo = repo

    async def execute(
        self, service_id: int, user_id: int, is_primary: bool = False
    ) -> ServiceEmployee:
        return await self._repo.assign(service_id=service_id, user_id=user_id, is_primary=is_primary)


class RemoveEmployeeUseCase:
    def __init__(self, repo: ServiceEmployeeRepository) -> None:
        self._repo = repo

    async def execute(self, employee_id: int) -> None:
        removed = await self._repo.remove(employee_id)
        if not removed:
            raise ServiceEmployeeNotFoundError(employee_id)


# ---------------------------------------------------------------------------
# Galleries
# ---------------------------------------------------------------------------

class AddGalleryImageUseCase:
    def __init__(self, repo: ServiceGalleryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        service_id: int,
        image: str,
        caption: str | None = None,
        sort_order: int = 0,
    ) -> ServiceGallery:
        return await self._repo.add_image(
            service_id=service_id, image=image, caption=caption, sort_order=sort_order
        )


class DeleteGalleryImageUseCase:
    def __init__(self, repo: ServiceGalleryRepository) -> None:
        self._repo = repo

    async def execute(self, gallery_id: int) -> None:
        deleted = await self._repo.delete(gallery_id)
        if not deleted:
            raise ServiceGalleryNotFoundError(gallery_id)


class ReorderGalleryUseCase:
    def __init__(self, repo: ServiceGalleryRepository) -> None:
        self._repo = repo

    async def execute(self, items: list[dict]) -> None:
        await self._repo.reorder(items)


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

class ListReviewsUseCase:
    def __init__(self, repo: ServiceReviewRepository) -> None:
        self._repo = repo

    async def execute(self, service_id: int, params: PaginationParams) -> Page[ServiceReview]:
        items, total = await self._repo.list_approved(service_id, params)
        return Page.create(data=items, total=total, params=params)


class CreateReviewUseCase:
    def __init__(self, repo: ServiceReviewRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        service_id: int,
        user_id: int,
        rating: int,
        comment: str | None = None,
    ) -> ServiceReview:
        if await self._repo.user_has_review(service_id=service_id, user_id=user_id):
            raise DuplicateReviewError(user_id=user_id, service_id=service_id)
        return await self._repo.create(
            service_id=service_id, user_id=user_id, rating=rating, comment=comment
        )
