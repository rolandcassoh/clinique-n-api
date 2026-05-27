class DomainException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EntityNotFoundError(DomainException):
    def __init__(self, entity: str, identifier: str | int) -> None:
        super().__init__(f"{entity} with id '{identifier}' not found.")
        self.entity = entity
        self.identifier = identifier


class ValidationError(DomainException):
    pass


class ConflictError(DomainException):
    pass


class AuthorizationError(DomainException):
    pass


class BusinessRuleViolationError(DomainException):
    pass
