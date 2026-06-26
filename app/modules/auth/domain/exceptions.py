from app.shared.exceptions.domain import DomainException


class InvalidCredentialsError(DomainException):
    def __init__(self) -> None:
        super().__init__("Email ou mot de passe incorrect.")


class UserNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Utilisateur '{identifier}' introuvable.")


class UserAlreadyExistsError(DomainException):
    def __init__(self, courriel: str) -> None:
        super().__init__(f"Un utilisateur avec l'courriel '{courriel}' existe déjà.")


class EmailNotVerifiedError(DomainException):
    def __init__(self) -> None:
        super().__init__("L'adresse courriel n'a pas encore été vérifiée.")


class AccountInactiveError(DomainException):
    def __init__(self) -> None:
        super().__init__("Ce compte est inactif.")


class InvalidOtpError(DomainException):
    def __init__(self) -> None:
        super().__init__("Code OTP invalide ou expiré.")


class InvalidTotpError(DomainException):
    def __init__(self) -> None:
        super().__init__("Jeton TOTP invalide.")


class TotpAlreadyEnabledError(DomainException):
    def __init__(self) -> None:
        super().__init__("L'authentification à deux facteurs est déjà activée.")


class InvalidResetTokenError(DomainException):
    def __init__(self) -> None:
        super().__init__("Jeton de réinitialisation du mot de passe invalide ou expiré.")
