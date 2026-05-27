from app.shared.exceptions.domain import DomainException


class SubscriptionPlanNotFoundError(DomainException):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"SubscriptionPlan '{identifier}' not found.")


class SubscriptionNotFoundError(DomainException):
    def __init__(self, subscription_id: int) -> None:
        super().__init__(f"Subscription '{subscription_id}' not found.")


class ActiveSubscriptionExistsError(DomainException):
    def __init__(self, clinic_id: int) -> None:
        super().__init__(
            f"Clinic '{clinic_id}' already has an active or trial subscription."
        )


class CannotRenewCancelledError(DomainException):
    def __init__(self, subscription_id: int) -> None:
        super().__init__(
            f"Cannot renew cancelled subscription '{subscription_id}'."
        )


class PlanLimitationNotFoundError(DomainException):
    def __init__(self, plan_id: int, feature: str) -> None:
        super().__init__(
            f"Limitation '{feature}' not found on plan '{plan_id}'."
        )
