from app.shared.exceptions.domain import DomainException


class VitalSignsNotFoundError(DomainException):
    def __init__(self, vital_id: int) -> None:
        super().__init__(f"VitalSigns '{vital_id}' not found.")
        self.vital_id = vital_id


class VitalSignsAccessDeniedError(DomainException):
    def __init__(self, vital_id: int) -> None:
        super().__init__(f"Access denied to VitalSigns '{vital_id}'.")
        self.vital_id = vital_id
