"""Router FastAPI du module Service."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.service.api.schemas import (
    GalleryReorderRequest,
    ServiceCategoryCreateRequest,
    ServiceCategorySchema,
    ServiceCategoryUpdateRequest,
    ServiceCreateRequest,
    ServiceEmployeeAssignRequest,
    ServiceEmployeeSchema,
    ServiceGalleryCreateRequest,
    ServiceGallerySchema,
    ServicePackageCreateRequest,
    ServicePackageSchema,
    ServicePackageUpdateRequest,
    ServiceReviewCreateRequest,
    ServiceReviewSchema,
    ServiceSchema,
    ServiceUpdateRequest,
)
from app.modules.service.application.use_cases import (
    AddGalleryImageUseCase,
    AssignEmployeeUseCase,
    CreateCategoryUseCase,
    CreatePackageUseCase,
    CreateReviewUseCase,
    CreateServiceUseCase,
    DeleteCategoryUseCase,
    DeleteGalleryImageUseCase,
    DeletePackageUseCase,
    DeleteServiceUseCase,
    GetCategoryBySlugUseCase,
    GetServiceBySlugUseCase,
    ListActiveCategoriesUseCase,
    ListPackagesUseCase,
    ListReviewsUseCase,
    ListServicesUseCase,
    RemoveEmployeeUseCase,
    ReorderGalleryUseCase,
    ToggleServiceUseCase,
    UpdateCategoryUseCase,
    UpdatePackageUseCase,
    UpdateServiceUseCase,
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
from app.modules.service.infrastructure.repositories import (
    SQLAlchemyServiceCategoryRepository,
    SQLAlchemyServiceEmployeeRepository,
    SQLAlchemyServiceGalleryRepository,
    SQLAlchemyServicePackageRepository,
    SQLAlchemyServiceRepository,
    SQLAlchemyServiceReviewRepository,
)
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Services"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]
UserDep = Annotated[dict[str, Any], Depends(get_current_user)]


# ---------------------------------------------------------------------------
# Dependency factories
# ---------------------------------------------------------------------------

def _cat_repo(db: DbDep) -> SQLAlchemyServiceCategoryRepository:
    return SQLAlchemyServiceCategoryRepository(db)

def _svc_repo(db: DbDep) -> SQLAlchemyServiceRepository:
    return SQLAlchemyServiceRepository(db)

def _pkg_repo(db: DbDep) -> SQLAlchemyServicePackageRepository:
    return SQLAlchemyServicePackageRepository(db)

def _emp_repo(db: DbDep) -> SQLAlchemyServiceEmployeeRepository:
    return SQLAlchemyServiceEmployeeRepository(db)

def _gallery_repo(db: DbDep) -> SQLAlchemyServiceGalleryRepository:
    return SQLAlchemyServiceGalleryRepository(db)

def _review_repo(db: DbDep) -> SQLAlchemyServiceReviewRepository:
    return SQLAlchemyServiceReviewRepository(db)


# ---------------------------------------------------------------------------
# Public — Categories
# ---------------------------------------------------------------------------

@router.get("/service-categories", response_model=Page[ServiceCategorySchema])
async def list_service_categories(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> Page[ServiceCategorySchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListActiveCategoriesUseCase(repo)
    return await uc.execute(params)  # type: ignore[return-value]


@router.get("/service-categories/{slug}", response_model=ServiceCategorySchema)
async def get_service_category(
    slug: str,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> ServiceCategorySchema:
    uc = GetCategoryBySlugUseCase(repo)
    try:
        cat = await uc.execute(slug)
    except (ServiceCategoryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ServiceCategorySchema.model_validate(cat)


# ---------------------------------------------------------------------------
# Public — Services
# ---------------------------------------------------------------------------

@router.get("/services", response_model=Page[ServiceSchema])
async def list_services(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    category_id: Annotated[int | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    is_home_service: Annotated[bool | None, Query()] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> Page[ServiceSchema]:
    from decimal import Decimal
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListServicesUseCase(repo)
    return await uc.execute(  # type: ignore[return-value]
        params=params,
        category_id=category_id,
        search=search,
        is_home_service=is_home_service,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
    )


@router.get("/services/{slug}", response_model=ServiceSchema)
async def get_service(
    slug: str,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = GetServiceBySlugUseCase(repo)
    try:
        svc = await uc.execute(slug)
    except (ServiceNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ServiceSchema.model_validate(svc)


# ---------------------------------------------------------------------------
# Public — Reviews
# ---------------------------------------------------------------------------

@router.get("/services/{service_id}/reviews", response_model=Page[ServiceReviewSchema])
async def list_reviews(
    service_id: int,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyServiceReviewRepository = Depends(_review_repo),
) -> Page[ServiceReviewSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListReviewsUseCase(repo)
    return await uc.execute(service_id=service_id, params=params)  # type: ignore[return-value]


@router.post(
    "/services/{service_id}/reviews",
    response_model=ServiceReviewSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    service_id: int,
    payload: ServiceReviewCreateRequest,
    current_user: UserDep,
    repo: SQLAlchemyServiceReviewRepository = Depends(_review_repo),
) -> ServiceReviewSchema:
    uc = CreateReviewUseCase(repo)
    try:
        review = await uc.execute(
            service_id=service_id,
            user_id=current_user["id"],
            rating=payload.rating,
            comment=payload.comment,
        )
    except DuplicateReviewError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceReviewSchema.model_validate(review)


# ---------------------------------------------------------------------------
# Admin — Services
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services",
    response_model=ServiceSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_service(
    payload: ServiceCreateRequest,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = CreateServiceUseCase(repo)
    try:
        svc = await uc.execute(**payload.model_dump())
    except ServiceSlugConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


@router.put(
    "/admin/services/{service_id}",
    response_model=ServiceSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_service(
    service_id: int,
    payload: ServiceUpdateRequest,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = UpdateServiceUseCase(repo)
    try:
        svc = await uc.execute(service_id=service_id, **payload.model_dump())
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ServiceSlugConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


@router.delete(
    "/admin/services/{service_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_service(
    service_id: int,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> None:
    uc = DeleteServiceUseCase(repo)
    try:
        await uc.execute(service_id)
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.patch(
    "/admin/services/{service_id}/toggle",
    response_model=ServiceSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_toggle_service(
    service_id: int,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = ToggleServiceUseCase(repo)
    try:
        svc = await uc.execute(service_id)
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


# ---------------------------------------------------------------------------
# Admin — Packages
# ---------------------------------------------------------------------------

@router.get(
    "/admin/services/{service_id}/packages",
    response_model=list[ServicePackageSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_packages(
    service_id: int,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> list[ServicePackageSchema]:
    uc = ListPackagesUseCase(repo)
    pkgs = await uc.execute(service_id)
    return [ServicePackageSchema.model_validate(p) for p in pkgs]


@router.post(
    "/admin/services/{service_id}/packages",
    response_model=ServicePackageSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_package(
    service_id: int,
    payload: ServicePackageCreateRequest,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> ServicePackageSchema:
    uc = CreatePackageUseCase(repo)
    pkg = await uc.execute(service_id=service_id, **payload.model_dump())
    return ServicePackageSchema.model_validate(pkg)


@router.put(
    "/admin/services/{service_id}/packages/{pkg_id}",
    response_model=ServicePackageSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_package(
    service_id: int,
    pkg_id: int,
    payload: ServicePackageUpdateRequest,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> ServicePackageSchema:
    uc = UpdatePackageUseCase(repo)
    try:
        pkg = await uc.execute(package_id=pkg_id, **payload.model_dump())
    except ServicePackageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ServicePackageSchema.model_validate(pkg)


@router.delete(
    "/admin/services/{service_id}/packages/{pkg_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_package(
    service_id: int,
    pkg_id: int,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> None:
    uc = DeletePackageUseCase(repo)
    try:
        await uc.execute(pkg_id)
    except ServicePackageNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin — Employees
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services/{service_id}/employees",
    response_model=ServiceEmployeeSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_assign_employee(
    service_id: int,
    payload: ServiceEmployeeAssignRequest,
    repo: SQLAlchemyServiceEmployeeRepository = Depends(_emp_repo),
) -> ServiceEmployeeSchema:
    uc = AssignEmployeeUseCase(repo)
    emp = await uc.execute(service_id=service_id, **payload.model_dump())
    return ServiceEmployeeSchema.model_validate(emp)


@router.delete(
    "/admin/services/{service_id}/employees/{emp_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_remove_employee(
    service_id: int,
    emp_id: int,
    repo: SQLAlchemyServiceEmployeeRepository = Depends(_emp_repo),
) -> None:
    uc = RemoveEmployeeUseCase(repo)
    try:
        await uc.execute(emp_id)
    except ServiceEmployeeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin — Galleries
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services/{service_id}/galleries",
    response_model=ServiceGallerySchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_add_gallery_image(
    service_id: int,
    payload: ServiceGalleryCreateRequest,
    repo: SQLAlchemyServiceGalleryRepository = Depends(_gallery_repo),
) -> ServiceGallerySchema:
    uc = AddGalleryImageUseCase(repo)
    img = await uc.execute(service_id=service_id, **payload.model_dump())
    return ServiceGallerySchema.model_validate(img)


@router.delete(
    "/admin/services/{service_id}/galleries/{img_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_gallery_image(
    service_id: int,
    img_id: int,
    repo: SQLAlchemyServiceGalleryRepository = Depends(_gallery_repo),
) -> None:
    uc = DeleteGalleryImageUseCase(repo)
    try:
        await uc.execute(img_id)
    except ServiceGalleryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.patch(
    "/admin/services/{service_id}/galleries/reorder",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_reorder_gallery(
    service_id: int,
    payload: GalleryReorderRequest,
    repo: SQLAlchemyServiceGalleryRepository = Depends(_gallery_repo),
) -> None:
    uc = ReorderGalleryUseCase(repo)
    await uc.execute([item.model_dump() for item in payload.items])


# ---------------------------------------------------------------------------
# Admin — Categories
# ---------------------------------------------------------------------------

@router.post(
    "/admin/service-categories",
    response_model=ServiceCategorySchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_category(
    payload: ServiceCategoryCreateRequest,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> ServiceCategorySchema:
    uc = CreateCategoryUseCase(repo)
    try:
        cat = await uc.execute(**payload.model_dump())
    except CategorySlugConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceCategorySchema.model_validate(cat)


@router.put(
    "/admin/service-categories/{category_id}",
    response_model=ServiceCategorySchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_category(
    category_id: int,
    payload: ServiceCategoryUpdateRequest,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> ServiceCategorySchema:
    uc = UpdateCategoryUseCase(repo)
    try:
        cat = await uc.execute(category_id=category_id, **payload.model_dump())
    except ServiceCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except CategorySlugConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceCategorySchema.model_validate(cat)


@router.delete(
    "/admin/service-categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_category(
    category_id: int,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> None:
    uc = DeleteCategoryUseCase(repo)
    try:
        await uc.execute(category_id)
    except ServiceCategoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message) from exc
