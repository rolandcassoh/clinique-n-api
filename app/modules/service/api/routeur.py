"""Router FastAPI du module Service."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
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
from app.modules.service.application.cas_utilisation import (
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
from app.modules.service.infrastructure.depots import (
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
    return await uc.execute(params)  # type: ignore[return-valeur]


@router.get("/service-categories/{identifiant_url}", response_model=ServiceCategorySchema)
async def get_service_category(
    identifiant_url: str,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> ServiceCategorySchema:
    uc = GetCategoryBySlugUseCase(repo)
    try:
        cat = await uc.execute(identifiant_url)
    except (ServiceCategoryNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ServiceCategorySchema.model_validate(cat)


# ---------------------------------------------------------------------------
# Public — Services
# ---------------------------------------------------------------------------

@router.get("/services", response_model=Page[ServiceSchema])
async def list_services(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    id_categorie: Annotated[int | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    service_domicile: Annotated[bool | None, Query()] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> Page[ServiceSchema]:
    from decimal import Decimal
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListServicesUseCase(repo)
    return await uc.execute(  # type: ignore[return-valeur]
        params=params,
        id_categorie=id_categorie,
        search=search,
        service_domicile=service_domicile,
        min_price=Decimal(str(min_price)) if min_price is not None else None,
        max_price=Decimal(str(max_price)) if max_price is not None else None,
    )


@router.get("/services/{identifiant_url}", response_model=ServiceSchema)
async def get_service(
    identifiant_url: str,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = GetServiceBySlugUseCase(repo)
    try:
        svc = await uc.execute(identifiant_url)
    except (ServiceNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ServiceSchema.model_validate(svc)


# ---------------------------------------------------------------------------
# Public — Reviews
# ---------------------------------------------------------------------------

@router.get("/services/{id_service}/avis", response_model=Page[ServiceReviewSchema])
async def list_reviews(
    id_service: int,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyServiceReviewRepository = Depends(_review_repo),
) -> Page[ServiceReviewSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListReviewsUseCase(repo)
    return await uc.execute(id_service=id_service, params=params)  # type: ignore[return-valeur]


@router.post(
    "/services/{id_service}/avis",
    response_model=ServiceReviewSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_review(
    id_service: int,
    payload: ServiceReviewCreateRequest,
    current_user: UserDep,
    repo: SQLAlchemyServiceReviewRepository = Depends(_review_repo),
) -> ServiceReviewSchema:
    uc = CreateReviewUseCase(repo)
    try:
        review = await uc.execute(
            id_service=id_service,
            id_utilisateur=current_user["id"],
            note=payload.note,
            commentaire=payload.commentaire,
        )
    except DuplicateReviewError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceReviewSchema.model_validate(review)


# ---------------------------------------------------------------------------
# Admin — Services
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services",
    response_model=ServiceSchema,
    status_code=statut.HTTP_201_CREATED,
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
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


@router.put(
    "/admin/services/{id_service}",
    response_model=ServiceSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_service(
    id_service: int,
    payload: ServiceUpdateRequest,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = UpdateServiceUseCase(repo)
    try:
        svc = await uc.execute(id_service=id_service, **payload.model_dump())
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except ServiceSlugConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


@router.delete(
    "/admin/services/{id_service}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_service(
    id_service: int,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> None:
    uc = DeleteServiceUseCase(repo)
    try:
        await uc.execute(id_service)
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.patch(
    "/admin/services/{id_service}/basculer",
    response_model=ServiceSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_toggle_service(
    id_service: int,
    repo: SQLAlchemyServiceRepository = Depends(_svc_repo),
) -> ServiceSchema:
    uc = ToggleServiceUseCase(repo)
    try:
        svc = await uc.execute(id_service)
    except ServiceNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ServiceSchema.model_validate(svc)


# ---------------------------------------------------------------------------
# Admin — Packages
# ---------------------------------------------------------------------------

@router.get(
    "/admin/services/{id_service}/packages",
    response_model=list[ServicePackageSchema],
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_list_packages(
    id_service: int,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> list[ServicePackageSchema]:
    uc = ListPackagesUseCase(repo)
    pkgs = await uc.execute(id_service)
    return [ServicePackageSchema.model_validate(p) for p in pkgs]


@router.post(
    "/admin/services/{id_service}/packages",
    response_model=ServicePackageSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_create_package(
    id_service: int,
    payload: ServicePackageCreateRequest,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> ServicePackageSchema:
    uc = CreatePackageUseCase(repo)
    pkg = await uc.execute(id_service=id_service, **payload.model_dump())
    return ServicePackageSchema.model_validate(pkg)


@router.put(
    "/admin/services/{id_service}/packages/{pkg_id}",
    response_model=ServicePackageSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_package(
    id_service: int,
    pkg_id: int,
    payload: ServicePackageUpdateRequest,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> ServicePackageSchema:
    uc = UpdatePackageUseCase(repo)
    try:
        pkg = await uc.execute(package_id=pkg_id, **payload.model_dump())
    except ServicePackageNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    return ServicePackageSchema.model_validate(pkg)


@router.delete(
    "/admin/services/{id_service}/packages/{pkg_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_package(
    id_service: int,
    pkg_id: int,
    repo: SQLAlchemyServicePackageRepository = Depends(_pkg_repo),
) -> None:
    uc = DeletePackageUseCase(repo)
    try:
        await uc.execute(pkg_id)
    except ServicePackageNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin — Employees
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services/{id_service}/employees",
    response_model=ServiceEmployeeSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_assign_employee(
    id_service: int,
    payload: ServiceEmployeeAssignRequest,
    repo: SQLAlchemyServiceEmployeeRepository = Depends(_emp_repo),
) -> ServiceEmployeeSchema:
    uc = AssignEmployeeUseCase(repo)
    emp = await uc.execute(id_service=id_service, **payload.model_dump())
    return ServiceEmployeeSchema.model_validate(emp)


@router.delete(
    "/admin/services/{id_service}/employees/{emp_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_remove_employee(
    id_service: int,
    emp_id: int,
    repo: SQLAlchemyServiceEmployeeRepository = Depends(_emp_repo),
) -> None:
    uc = RemoveEmployeeUseCase(repo)
    try:
        await uc.execute(emp_id)
    except ServiceEmployeeNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc


# ---------------------------------------------------------------------------
# Admin — Galleries
# ---------------------------------------------------------------------------

@router.post(
    "/admin/services/{id_service}/galeries",
    response_model=ServiceGallerySchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_add_gallery_image(
    id_service: int,
    payload: ServiceGalleryCreateRequest,
    repo: SQLAlchemyServiceGalleryRepository = Depends(_gallery_repo),
) -> ServiceGallerySchema:
    uc = AddGalleryImageUseCase(repo)
    img = await uc.execute(id_service=id_service, **payload.model_dump())
    return ServiceGallerySchema.model_validate(img)


@router.delete(
    "/admin/services/{id_service}/galeries/{img_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_gallery_image(
    id_service: int,
    img_id: int,
    repo: SQLAlchemyServiceGalleryRepository = Depends(_gallery_repo),
) -> None:
    uc = DeleteGalleryImageUseCase(repo)
    try:
        await uc.execute(img_id)
    except ServiceGalleryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc


@router.patch(
    "/admin/services/{id_service}/galeries/reordonner",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_reorder_gallery(
    id_service: int,
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
    status_code=statut.HTTP_201_CREATED,
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
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceCategorySchema.model_validate(cat)


@router.put(
    "/admin/service-categories/{id_categorie}",
    response_model=ServiceCategorySchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_update_category(
    id_categorie: int,
    payload: ServiceCategoryUpdateRequest,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> ServiceCategorySchema:
    uc = UpdateCategoryUseCase(repo)
    try:
        cat = await uc.execute(id_categorie=id_categorie, **payload.model_dump())
    except ServiceCategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc
    except CategorySlugConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=exc.message) from exc
    return ServiceCategorySchema.model_validate(cat)


@router.delete(
    "/admin/service-categories/{id_categorie}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def admin_delete_category(
    id_categorie: int,
    repo: SQLAlchemyServiceCategoryRepository = Depends(_cat_repo),
) -> None:
    uc = DeleteCategoryUseCase(repo)
    try:
        await uc.execute(id_categorie)
    except ServiceCategoryNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message) from exc
