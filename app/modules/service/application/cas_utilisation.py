"""Use Cases du module Service."""
from __future__ import annotations

from decimal import Decimal

from app.modules.service.domain.entites import (
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
from app.modules.service.domain.depots import (
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

    async def execute(self, identifiant_url: str) -> ServiceCategory:
        cat = await self._repo.get_by_slug(identifiant_url)
        if cat is None:
            raise ServiceCategoryNotFoundError(identifiant_url)
        return cat


class CreateCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        nom: str,
        identifiant_url: str,
        image: str | None = None,
        description: str | None = None,
        est_actif: bool = True,
        ordre_affichage: int = 0,
    ) -> ServiceCategory:
        if await self._repo.slug_exists(identifiant_url):
            raise CategorySlugConflictError(identifiant_url)
        return await self._repo.create(
            nom=nom, identifiant_url=identifiant_url, image=image, description=description,
            est_actif=est_actif, ordre_affichage=ordre_affichage,
        )


class UpdateCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_categorie: int,
        nom: str | None = None,
        identifiant_url: str | None = None,
        image: str | None = None,
        description: str | None = None,
        est_actif: bool | None = None,
        ordre_affichage: int | None = None,
    ) -> ServiceCategory:
        if identifiant_url and await self._repo.slug_exists(identifiant_url, exclude_id=id_categorie):
            raise CategorySlugConflictError(identifiant_url)
        cat = await self._repo.update(
            id_categorie=id_categorie, nom=nom, identifiant_url=identifiant_url, image=image,
            description=description, est_actif=est_actif, ordre_affichage=ordre_affichage,
        )
        if cat is None:
            raise ServiceCategoryNotFoundError(id_categorie)
        return cat


class DeleteCategoryUseCase:
    def __init__(self, repo: ServiceCategoryRepository) -> None:
        self._repo = repo

    async def execute(self, id_categorie: int) -> None:
        deleted = await self._repo.soft_delete(id_categorie)
        if not deleted:
            raise ServiceCategoryNotFoundError(id_categorie)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------

class ListServicesUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        params: PaginationParams,
        id_categorie: int | None = None,
        search: str | None = None,
        service_domicile: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> Page[Service]:
        items, total = await self._repo.list_public(
            params=params,
            id_categorie=id_categorie,
            search=search,
            service_domicile=service_domicile,
            min_price=min_price,
            max_price=max_price,
        )
        return Page.create(data=items, total=total, params=params)


class GetServiceBySlugUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, identifiant_url: str) -> Service:
        service = await self._repo.get_by_slug(identifiant_url)
        if service is None:
            raise ServiceNotFoundError(identifiant_url)
        return service


class CreateServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_prestataire: int,
        nom: str,
        identifiant_url: str,
        prix: Decimal,
        id_categorie: int | None = None,
        description: str | None = None,
        short_description: str | None = None,
        prix_remise: Decimal | None = None,
        duree_minutes: int = 60,
        est_actif: bool = True,
        est_mis_en_avant: bool = False,
        service_domicile: bool = False,
        max_membres: int = 1,
    ) -> Service:
        if await self._repo.slug_exists(identifiant_url):
            raise ServiceSlugConflictError(identifiant_url)
        return await self._repo.create(
            id_prestataire=id_prestataire, id_categorie=id_categorie, nom=nom, identifiant_url=identifiant_url,
            description=description, short_description=short_description,
            prix=prix, prix_remise=prix_remise, duree_minutes=duree_minutes,
            est_actif=est_actif, est_mis_en_avant=est_mis_en_avant, service_domicile=service_domicile,
            max_membres=max_membres,
        )


class UpdateServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_service: int,
        id_prestataire: int | None = None,
        id_categorie: int | None = None,
        nom: str | None = None,
        identifiant_url: str | None = None,
        description: str | None = None,
        short_description: str | None = None,
        prix: Decimal | None = None,
        prix_remise: Decimal | None = None,
        duree_minutes: int | None = None,
        est_actif: bool | None = None,
        est_mis_en_avant: bool | None = None,
        service_domicile: bool | None = None,
        max_membres: int | None = None,
    ) -> Service:
        if identifiant_url and await self._repo.slug_exists(identifiant_url, exclude_id=id_service):
            raise ServiceSlugConflictError(identifiant_url)
        service = await self._repo.update(
            id_service=id_service, id_prestataire=id_prestataire, id_categorie=id_categorie,
            nom=nom, identifiant_url=identifiant_url, description=description, short_description=short_description,
            prix=prix, prix_remise=prix_remise, duree_minutes=duree_minutes,
            est_actif=est_actif, est_mis_en_avant=est_mis_en_avant, service_domicile=service_domicile,
            max_membres=max_membres,
        )
        if service is None:
            raise ServiceNotFoundError(id_service)
        return service


class DeleteServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, id_service: int) -> None:
        deleted = await self._repo.soft_delete(id_service)
        if not deleted:
            raise ServiceNotFoundError(id_service)


class ToggleServiceUseCase:
    def __init__(self, repo: ServiceRepository) -> None:
        self._repo = repo

    async def execute(self, id_service: int) -> Service:
        service = await self._repo.get_by_id(id_service)
        if service is None:
            raise ServiceNotFoundError(id_service)
        updated = await self._repo.update(
            id_service=id_service, id_prestataire=None, id_categorie=None, nom=None,
            identifiant_url=None, description=None, short_description=None, prix=None,
            prix_remise=None, duree_minutes=None, est_actif=not service.est_actif,
            est_mis_en_avant=None, service_domicile=None, max_membres=None,
        )
        if updated is None:
            raise ServiceNotFoundError(id_service)
        return updated


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class ListPackagesUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(self, id_service: int) -> list[ServicePackage]:
        return await self._repo.list_by_service(id_service)


class CreatePackageUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_service: int,
        nom: str,
        prix: Decimal,
        nombre_seances: int = 1,
        jours_validite: int = 30,
        description: str | None = None,
        est_actif: bool = True,
    ) -> ServicePackage:
        return await self._repo.create(
            id_service=id_service, nom=nom, description=description,
            prix=prix, nombre_seances=nombre_seances, jours_validite=jours_validite,
            est_actif=est_actif,
        )


class UpdatePackageUseCase:
    def __init__(self, repo: ServicePackageRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        package_id: int,
        nom: str | None = None,
        description: str | None = None,
        prix: Decimal | None = None,
        nombre_seances: int | None = None,
        jours_validite: int | None = None,
        est_actif: bool | None = None,
    ) -> ServicePackage:
        pkg = await self._repo.update(
            package_id=package_id, nom=nom, description=description,
            prix=prix, nombre_seances=nombre_seances, jours_validite=jours_validite,
            est_actif=est_actif,
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
        self, id_service: int, id_utilisateur: int, est_principal: bool = False
    ) -> ServiceEmployee:
        return await self._repo.assign(id_service=id_service, id_utilisateur=id_utilisateur, est_principal=est_principal)


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
        id_service: int,
        image: str,
        legende: str | None = None,
        ordre_affichage: int = 0,
    ) -> ServiceGallery:
        return await self._repo.add_image(
            id_service=id_service, image=image, legende=legende, ordre_affichage=ordre_affichage
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

    async def execute(self, id_service: int, params: PaginationParams) -> Page[ServiceReview]:
        items, total = await self._repo.list_approved(id_service, params)
        return Page.create(data=items, total=total, params=params)


class CreateReviewUseCase:
    def __init__(self, repo: ServiceReviewRepository) -> None:
        self._repo = repo

    async def execute(
        self,
        id_service: int,
        id_utilisateur: int,
        note: int,
        commentaire: str | None = None,
    ) -> ServiceReview:
        if await self._repo.user_has_review(id_service=id_service, id_utilisateur=id_utilisateur):
            raise DuplicateReviewError(id_utilisateur=id_utilisateur, id_service=id_service)
        return await self._repo.create(
            id_service=id_service, id_utilisateur=id_utilisateur, note=note, commentaire=commentaire
        )
