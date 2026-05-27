from app.shared.exceptions.domain import DomainException


class InvalidCredentialsError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid email or password.")


class UserNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"User '{identifier}' not found.")


class UserAlreadyExistsError(DomainException):
    def __init__(self, email: str) -> None:
        super().__init__(f"User with email '{email}' already exists.")


class EmailNotVerifiedError(DomainException):
    def __init__(self) -> None:
        super().__init__("Email address has not been verified.")


class AccountInactiveError(DomainException):
    def __init__(self) -> None:
        super().__init__("Account is inactive.")


class InvalidOtpError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid or expired OTP code.")


class InvalidTotpError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid TOTP token.")


class TotpAlreadyEnabledError(DomainException):
    def __init__(self) -> None:
        super().__init__("Two-factor authentication is already enabled.")


class InvalidResetTokenError(DomainException):
    def __init__(self) -> None:
        super().__init__("Invalid or expired password reset token.")
