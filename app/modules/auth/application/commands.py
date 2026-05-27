from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterCommand:
    name: str
    email: str
    password: str
    username: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True)
class ForgotPasswordCommand:
    email: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    token: str
    new_password: str


@dataclass(frozen=True)
class VerifyOtpCommand:
    user_id: int
    otp_code: str


@dataclass(frozen=True)
class SetupTotpCommand:
    user_id: int


@dataclass(frozen=True)
class VerifyTotpCommand:
    user_id: int
    token: str
