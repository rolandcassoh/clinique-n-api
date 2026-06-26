"""Exceptions métier du module Service."""
from app.shared.exceptions.domain import ConflictError, EntityNotFoundError


class ServiceNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: int | str) -> None:
        super().__init__("Service", identifier)


class ServiceCategoryNotFoundError(EntityNotFoundError):
    def __init__(self, identifier: int | str) -> None:
        super().__init__("ServiceCategory", identifier)


class ServicePackageNotFoundError(EntityNotFoundError):
    def __init__(self, package_id: int) -> None:
        super().__init__("ServicePackage", package_id)


class ServiceEmployeeNotFoundError(EntityNotFoundError):
    def __init__(self, employee_id: int) -> None:
        super().__init__("ServiceEmployee", employee_id)


class ServiceGalleryNotFoundError(EntityNotFoundError):
    def __init__(self, gallery_id: int) -> None:
        super().__init__("ServiceGallery", gallery_id)


class ServiceReviewNotFoundError(EntityNotFoundError):
    def __init__(self, review_id: int) -> None:
        super().__init__("ServiceReview", review_id)


class DuplicateReviewError(ConflictError):
    def __init__(self, id_utilisateur: int, id_service: int) -> None:
        super().__init__(
            f"L'utilisateur {id_utilisateur} a déjà soumis un avis pour le service {id_service}."
        )


class ServiceSlugConflictError(ConflictError):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Un service avec le identifiant_url '{identifiant_url}' existe déjà.")


class CategorySlugConflictError(ConflictError):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Une catégorie avec le identifiant_url '{identifiant_url}' existe déjà.")
