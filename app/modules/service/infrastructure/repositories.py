"""Implémentation SQLAlchemy async des repositories Service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.service.domain.entities import (
    Service,
    ServiceCategory,
    ServiceEmployee,
    ServiceGallery,
    ServicePackage,
    ServiceReview,
)
from app.modules.service.domain.repositories import (
    ServiceCategoryRepository,
    ServiceEmployeeRepository,
    ServiceGalleryRepository,
    ServicePackageRepository,
    ServiceRepository,
    ServiceReviewRepository,
)
from app.modules.service.infrastructure.models import (
    ServiceCategoryModel,
    ServiceEmployeeModel,
    ServiceGalleryModel,
    ServiceModel,
    ServicePackageModel,
    ServiceReviewModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------

def _cat_to_entity(m: ServiceCategoryModel) -> ServiceCategory:
    return ServiceCategory(
        id=m.id, name=m.name, slug=m.slug, image=m.image,
        description=m.description, is_active=m.is_active, sort_order=m.sort_order,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _pkg_to_entity(m: ServicePackageModel) -> ServicePackage:
    return ServicePackage(
        id=m.id, service_id=m.service_id, name=m.name, description=m.description,
        price=m.price, sessions_count=m.sessions_count, validity_days=m.validity_days,
        is_active=m.is_active, created_at=m.created_at, updated_at=m.updated_at,
    )


def _emp_to_entity(m: ServiceEmployeeModel) -> ServiceEmployee:
    return ServiceEmployee(
        id=m.id, service_id=m.service_id, user_id=m.user_id, is_primary=m.is_primary,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _gallery_to_entity(m: ServiceGalleryModel) -> ServiceGallery:
    return ServiceGallery(
        id=m.id, service_id=m.service_id, image=m.image, caption=m.caption,
        sort_order=m.sort_order, created_at=m.created_at, updated_at=m.updated_at,
    )


def _review_to_entity(m: ServiceReviewModel) -> ServiceReview:
    return ServiceReview(
        id=m.id, service_id=m.service_id, user_id=m.user_id, rating=m.rating,
        comment=m.comment, is_approved=m.is_approved,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _svc_to_entity(
    m: ServiceModel,
    avg_rating: float | None = None,
    review_count: int = 0,
) -> Service:
    cat = _cat_to_entity(m.category) if m.category else None
    galleries = [_gallery_to_entity(g) for g in (m.galleries or [])]
    packages = [_pkg_to_entity(p) for p in (m.packages or [])]
    employees = [_emp_to_entity(e) for e in (m.employees or [])]
    return Service(
        id=m.id, vendor_id=m.vendor_id, category_id=m.category_id,
        name=m.name, slug=m.slug, description=m.description,
        short_description=m.short_description, price=m.price,
        discount_price=m.discount_price, duration_minutes=m.duration_minutes,
        is_active=m.is_active, is_featured=m.is_featured,
        is_home_service=m.is_home_service, max_members=m.max_members,
        created_at=m.created_at, updated_at=m.updated_at,
        category=cat, galleries=galleries, packages=packages, employees=employees,
        average_rating=avg_rating, review_count=review_count,
    )


# ---------------------------------------------------------------------------
# ServiceCategory
# ---------------------------------------------------------------------------

class SQLAlchemyServiceCategoryRepository(ServiceCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, params: PaginationParams) -> tuple[list[ServiceCategory], int]:
        base_q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.deleted_at.is_(None),
            ServiceCategoryModel.is_active.is_(True),
        )
        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()
        rows_q = base_q.order_by(ServiceCategoryModel.sort_order, ServiceCategoryModel.id).offset(params.offset).limit(params.per_page)
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_cat_to_entity(r) for r in rows], total

    async def get_by_slug(self, slug: str) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.slug == slug,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(row) if row else None

    async def get_by_id(self, category_id: int) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == category_id,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(row) if row else None

    async def create(
        self, name: str, slug: str, image: str | None, description: str | None,
        is_active: bool, sort_order: int,
    ) -> ServiceCategory:
        m = ServiceCategoryModel(
            name=name, slug=slug, image=image, description=description,
            is_active=is_active, sort_order=sort_order,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _cat_to_entity(m)

    async def update(
        self, category_id: int, name: str | None, slug: str | None, image: str | None,
        description: str | None, is_active: bool | None, sort_order: int | None,
    ) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == category_id,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        if name is not None:
            row.name = name
        if slug is not None:
            row.slug = slug
        if image is not None:
            row.image = image
        if description is not None:
            row.description = description
        if is_active is not None:
            row.is_active = is_active
        if sort_order is not None:
            row.sort_order = sort_order
        await self._session.flush()
        await self._session.refresh(row)
        return _cat_to_entity(row)

    async def soft_delete(self, category_id: int) -> bool:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == category_id,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool:
        q = select(func.count()).select_from(ServiceCategoryModel).where(
            ServiceCategoryModel.slug == slug,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            q = q.where(ServiceCategoryModel.id != exclude_id)
        return (await self._session.execute(q)).scalar_one() > 0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class SQLAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self):
        return (
            select(ServiceModel)
            .where(ServiceModel.deleted_at.is_(None), ServiceModel.is_active.is_(True))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )

    async def list_public(
        self,
        params: PaginationParams,
        category_id: int | None = None,
        search: str | None = None,
        is_home_service: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> tuple[list[Service], int]:
        base_q = select(ServiceModel).where(
            ServiceModel.deleted_at.is_(None),
            ServiceModel.is_active.is_(True),
        )
        if category_id is not None:
            base_q = base_q.where(ServiceModel.category_id == category_id)
        if search is not None:
            base_q = base_q.where(ServiceModel.name.ilike(f"%{search}%"))
        if is_home_service is not None:
            base_q = base_q.where(ServiceModel.is_home_service == is_home_service)
        if min_price is not None:
            base_q = base_q.where(ServiceModel.price >= min_price)
        if max_price is not None:
            base_q = base_q.where(ServiceModel.price <= max_price)

        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()

        rows_q = (
            base_q.options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
            .order_by(ServiceModel.id)
            .offset(params.offset)
            .limit(params.per_page)
        )
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_svc_to_entity(r) for r in rows], total

    async def get_by_slug(self, slug: str) -> Service | None:
        q = (
            select(ServiceModel)
            .where(ServiceModel.slug == slug, ServiceModel.deleted_at.is_(None))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        avg_rating = await self.get_average_rating(row.id)
        review_count_q = select(func.count()).where(
            ServiceReviewModel.service_id == row.id,
            ServiceReviewModel.is_approved.is_(True),
        )
        review_count: int = (await self._session.execute(review_count_q)).scalar_one()
        return _svc_to_entity(row, avg_rating=avg_rating, review_count=review_count)

    async def get_by_id(self, service_id: int) -> Service | None:
        q = (
            select(ServiceModel)
            .where(ServiceModel.id == service_id, ServiceModel.deleted_at.is_(None))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _svc_to_entity(row) if row else None

    async def create(
        self, vendor_id: int, category_id: int | None, name: str, slug: str,
        description: str | None, short_description: str | None, price: Decimal,
        discount_price: Decimal | None, duration_minutes: int, is_active: bool,
        is_featured: bool, is_home_service: bool, max_members: int,
    ) -> Service:
        m = ServiceModel(
            vendor_id=vendor_id, category_id=category_id, name=name, slug=slug,
            description=description, short_description=short_description, price=price,
            discount_price=discount_price, duration_minutes=duration_minutes,
            is_active=is_active, is_featured=is_featured, is_home_service=is_home_service,
            max_members=max_members,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _svc_to_entity(m)

    async def update(
        self, service_id: int, vendor_id: int | None, category_id: int | None,
        name: str | None, slug: str | None, description: str | None,
        short_description: str | None, price: Decimal | None,
        discount_price: Decimal | None, duration_minutes: int | None,
        is_active: bool | None, is_featured: bool | None, is_home_service: bool | None,
        max_members: int | None,
    ) -> Service | None:
        q = select(ServiceModel).where(
            ServiceModel.id == service_id, ServiceModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        for attr, val in [
            ("vendor_id", vendor_id), ("category_id", category_id), ("name", name),
            ("slug", slug), ("description", description), ("short_description", short_description),
            ("price", price), ("discount_price", discount_price),
            ("duration_minutes", duration_minutes), ("is_active", is_active),
            ("is_featured", is_featured), ("is_home_service", is_home_service),
            ("max_members", max_members),
        ]:
            if val is not None:
                setattr(row, attr, val)
        await self._session.flush()
        await self._session.refresh(row)
        return _svc_to_entity(row)

    async def soft_delete(self, service_id: int) -> bool:
        q = select(ServiceModel).where(
            ServiceModel.id == service_id, ServiceModel.deleted_at.is_(None)
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def slug_exists(self, slug: str, exclude_id: int | None = None) -> bool:
        q = select(func.count()).select_from(ServiceModel).where(
            ServiceModel.slug == slug, ServiceModel.deleted_at.is_(None)
        )
        if exclude_id is not None:
            q = q.where(ServiceModel.id != exclude_id)
        return (await self._session.execute(q)).scalar_one() > 0

    async def get_average_rating(self, service_id: int) -> float | None:
        q = select(func.avg(ServiceReviewModel.rating)).where(
            ServiceReviewModel.service_id == service_id,
            ServiceReviewModel.is_approved.is_(True),
        )
        result = (await self._session.execute(q)).scalar_one_or_none()
        return float(result) if result is not None else None


# ---------------------------------------------------------------------------
# ServicePackage
# ---------------------------------------------------------------------------

class SQLAlchemyServicePackageRepository(ServicePackageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, service_id: int) -> list[ServicePackage]:
        q = select(ServicePackageModel).where(
            ServicePackageModel.service_id == service_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(q)).scalars().all()
        return [_pkg_to_entity(r) for r in rows]

    async def get_by_id(self, package_id: int) -> ServicePackage | None:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _pkg_to_entity(row) if row else None

    async def create(
        self, service_id: int, name: str, description: str | None, price: Decimal,
        sessions_count: int, validity_days: int, is_active: bool,
    ) -> ServicePackage:
        m = ServicePackageModel(
            service_id=service_id, name=name, description=description, price=price,
            sessions_count=sessions_count, validity_days=validity_days, is_active=is_active,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _pkg_to_entity(m)

    async def update(
        self, package_id: int, name: str | None, description: str | None,
        price: Decimal | None, sessions_count: int | None, validity_days: int | None,
        is_active: bool | None,
    ) -> ServicePackage | None:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return None
        for attr, val in [
            ("name", name), ("description", description), ("price", price),
            ("sessions_count", sessions_count), ("validity_days", validity_days),
            ("is_active", is_active),
        ]:
            if val is not None:
                setattr(row, attr, val)
        await self._session.flush()
        await self._session.refresh(row)
        return _pkg_to_entity(row)

    async def delete(self, package_id: int) -> bool:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        row.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# ServiceEmployee
# ---------------------------------------------------------------------------

class SQLAlchemyServiceEmployeeRepository(ServiceEmployeeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, service_id: int) -> list[ServiceEmployee]:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.service_id == service_id)
        rows = (await self._session.execute(q)).scalars().all()
        return [_emp_to_entity(r) for r in rows]

    async def get_by_id(self, employee_id: int) -> ServiceEmployee | None:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.id == employee_id)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _emp_to_entity(row) if row else None

    async def assign(self, service_id: int, user_id: int, is_primary: bool) -> ServiceEmployee:
        m = ServiceEmployeeModel(service_id=service_id, user_id=user_id, is_primary=is_primary)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _emp_to_entity(m)

    async def remove(self, employee_id: int) -> bool:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.id == employee_id)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# ServiceGallery
# ---------------------------------------------------------------------------

class SQLAlchemyServiceGalleryRepository(ServiceGalleryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, service_id: int) -> list[ServiceGallery]:
        q = select(ServiceGalleryModel).where(
            ServiceGalleryModel.service_id == service_id
        ).order_by(ServiceGalleryModel.sort_order)
        rows = (await self._session.execute(q)).scalars().all()
        return [_gallery_to_entity(r) for r in rows]

    async def get_by_id(self, gallery_id: int) -> ServiceGallery | None:
        q = select(ServiceGalleryModel).where(ServiceGalleryModel.id == gallery_id)
        row = (await self._session.execute(q)).scalar_one_or_none()
        return _gallery_to_entity(row) if row else None

    async def add_image(
        self, service_id: int, image: str, caption: str | None, sort_order: int,
    ) -> ServiceGallery:
        m = ServiceGalleryModel(
            service_id=service_id, image=image, caption=caption, sort_order=sort_order
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _gallery_to_entity(m)

    async def delete(self, gallery_id: int) -> bool:
        q = select(ServiceGalleryModel).where(ServiceGalleryModel.id == gallery_id)
        row = (await self._session.execute(q)).scalar_one_or_none()
        if row is None:
            return False
        await self._session.delete(row)
        await self._session.flush()
        return True

    async def reorder(self, items: list[dict]) -> None:
        for item in items:
            await self._session.execute(
                update(ServiceGalleryModel)
                .where(ServiceGalleryModel.id == item["id"])
                .values(sort_order=item["sort_order"])
            )
        await self._session.flush()


# ---------------------------------------------------------------------------
# ServiceReview
# ---------------------------------------------------------------------------

class SQLAlchemyServiceReviewRepository(ServiceReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved(
        self, service_id: int, params: PaginationParams
    ) -> tuple[list[ServiceReview], int]:
        base_q = select(ServiceReviewModel).where(
            ServiceReviewModel.service_id == service_id,
            ServiceReviewModel.is_approved.is_(True),
        )
        count_q = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(count_q)).scalar_one()
        rows_q = base_q.order_by(ServiceReviewModel.id.desc()).offset(params.offset).limit(params.per_page)
        rows = (await self._session.execute(rows_q)).scalars().all()
        return [_review_to_entity(r) for r in rows], total

    async def user_has_review(self, service_id: int, user_id: int) -> bool:
        q = select(func.count()).select_from(ServiceReviewModel).where(
            ServiceReviewModel.service_id == service_id,
            ServiceReviewModel.user_id == user_id,
        )
        return (await self._session.execute(q)).scalar_one() > 0

    async def create(
        self, service_id: int, user_id: int, rating: int, comment: str | None,
    ) -> ServiceReview:
        m = ServiceReviewModel(
            service_id=service_id, user_id=user_id, rating=rating,
            comment=comment, is_approved=False,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _review_to_entity(m)
