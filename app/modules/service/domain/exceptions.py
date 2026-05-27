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
    def __init__(self, user_id: int, service_id: int) -> None:
        super().__init__(
            f"User {user_id} already has a review for service {service_id}."
        )


class ServiceSlugConflictError(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A service with slug '{slug}' already exists.")


class CategorySlugConflictError(ConflictError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"A category with slug '{slug}' already exists.")
