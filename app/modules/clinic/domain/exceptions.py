from app.shared.exceptions.domain import DomainException


class ClinicNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Clinique '{identifier}' introuvable.")
        self.identifier = identifier


class ClinicCategoryNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Catégorie de clinique '{identifier}' introuvable.")


class ClinicServiceNotFoundError(DomainException):
    def __init__(self, id_service: int) -> None:
        super().__init__(f"Service de clinique '{id_service}' introuvable.")


class DoctorNotFoundError(DomainException):
    def __init__(self, id_medecin: int) -> None:
        super().__init__(f"Médecin '{id_medecin}' introuvable.")
        self.id_medecin = id_medecin


class DoctorSessionNotFoundError(DomainException):
    def __init__(self, session_id: int) -> None:
        super().__init__(f"Session médecin '{session_id}' introuvable.")


class DoctorLeaveNotFoundError(DomainException):
    def __init__(self, leave_id: int) -> None:
        super().__init__(f"Congé médecin '{leave_id}' introuvable.")


class DoctorRatingNotFoundError(DomainException):
    def __init__(self, rating_id: int) -> None:
        super().__init__(f"Note médecin '{rating_id}' introuvable.")


class ReceptionistNotFoundError(DomainException):
    def __init__(self, receptionist_id: int) -> None:
        super().__init__(f"Réceptionniste '{receptionist_id}' introuvable.")


class DuplicateRatingError(DomainException):
    def __init__(self, id_medecin: int, id_utilisateur: int) -> None:
        super().__init__(
            f"L'utilisateur '{id_utilisateur}' a déjà noté le médecin '{id_medecin}'."
        )


class SlugAlreadyExistsError(DomainException):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Le identifiant_url '{identifiant_url}' est déjà utilisé.")
        self.identifiant_url = identifiant_url
