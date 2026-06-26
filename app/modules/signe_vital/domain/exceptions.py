from app.shared.exceptions.domain import DomainException


class VitalSignsNotFoundError(DomainException):
    def __init__(self, vital_id: int) -> None:
        super().__init__(f"Constantes vitales '{vital_id}' introuvables.")
        self.vital_id = vital_id


class VitalSignsAccessDeniedError(DomainException):
    def __init__(self, vital_id: int) -> None:
        super().__init__(f"Accès refusé aux constantes vitales '{vital_id}'.")
        self.vital_id = vital_id
