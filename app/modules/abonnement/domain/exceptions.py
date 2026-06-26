from app.shared.exceptions.domain import DomainException


class SubscriptionPlanNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Plan d'abonnement '{identifier}' introuvable.")


class SubscriptionNotFoundError(DomainException):
    def __init__(self, subscription_id: int) -> None:
        super().__init__(f"Abonnement '{subscription_id}' introuvable.")


class ActiveSubscriptionExistsError(DomainException):
    def __init__(self, id_clinique: int) -> None:
        super().__init__(
            f"La clinique '{id_clinique}' possède déjà un abonnement actif ou en essai."
        )


class CannotRenewCancelledError(DomainException):
    def __init__(self, subscription_id: int) -> None:
        super().__init__(
            f"Impossible de renouveler l'abonnement annulé '{subscription_id}'."
        )


class PlanLimitationNotFoundError(DomainException):
    def __init__(self, id_plan: int, fonctionnalite: str) -> None:
        super().__init__(
            f"Limitation '{fonctionnalite}' introuvable sur le plan '{id_plan}'."
        )
