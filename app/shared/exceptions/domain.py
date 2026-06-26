class DomainException(Exception):
    """Exception de base pour toutes les erreurs du domaine métier."""
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class EntityNotFoundError(DomainException):
    """Entité introuvable en base de données."""
    def __init__(self, entity: str, identifier: str | int) -> None:
        super().__init__(f"{entity} avec l'identifiant '{identifier}' introuvable.")
        self.entity = entity
        self.identifier = identifier


class ValidationError(DomainException):
    """Erreur de validation des données métier."""
    pass


class ConflictError(DomainException):
    """Conflit de données (doublon ou état incompatible)."""
    pass


class AuthorizationError(DomainException):
    """Accès non autorisé à une ressource."""
    pass


class BusinessRuleViolationError(DomainException):
    """Violation d'une règle métier."""
    pass
