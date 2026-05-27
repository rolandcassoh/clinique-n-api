from app.shared.exceptions.domain import DomainException


class ClinicNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Clinic '{identifier}' not found.")
        self.identifier = identifier


class ClinicCategoryNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"ClinicCategory '{identifier}' not found.")


class ClinicServiceNotFoundError(DomainException):
    def __init__(self, service_id: int) -> None:
        super().__init__(f"ClinicService '{service_id}' not found.")


class DoctorNotFoundError(DomainException):
    def __init__(self, doctor_id: int) -> None:
        super().__init__(f"Doctor '{doctor_id}' not found.")
        self.doctor_id = doctor_id


class DoctorSessionNotFoundError(DomainException):
    def __init__(self, session_id: int) -> None:
        super().__init__(f"DoctorSession '{session_id}' not found.")


class DoctorLeaveNotFoundError(DomainException):
    def __init__(self, leave_id: int) -> None:
        super().__init__(f"DoctorLeave '{leave_id}' not found.")


class DoctorRatingNotFoundError(DomainException):
    def __init__(self, rating_id: int) -> None:
        super().__init__(f"DoctorRating '{rating_id}' not found.")


class ReceptionistNotFoundError(DomainException):
    def __init__(self, receptionist_id: int) -> None:
        super().__init__(f"Receptionist '{receptionist_id}' not found.")


class DuplicateRatingError(DomainException):
    def __init__(self, doctor_id: int, user_id: int) -> None:
        super().__init__(
            f"User '{user_id}' already rated doctor '{doctor_id}'."
        )


class SlugAlreadyExistsError(DomainException):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Slug '{slug}' is already taken.")
        self.slug = slug
