from app.shared.exceptions.domain import DomainException


class PromotionNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Promotion '{identifier}' introuvable.")
        self.identifier = identifier


class PromotionCodeConflictError(DomainException):
    def __init__(self, code: str) -> None:
        super().__init__(f"Le code promotion '{code}' existe déjà.")
        self.code = code
