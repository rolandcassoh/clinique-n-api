from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterCommand:
    nom: str
    courriel: str
    mot_de_passe: str
    nom_utilisateur: str | None = None
    telephone: str | None = None


@dataclass(frozen=True)
class LoginCommand:
    courriel: str
    mot_de_passe: str


@dataclass(frozen=True)
class RefreshTokenCommand:
    refresh_token: str


@dataclass(frozen=True)
class ForgotPasswordCommand:
    courriel: str


@dataclass(frozen=True)
class ResetPasswordCommand:
    jeton: str
    new_password: str


@dataclass(frozen=True)
class VerifyOtpCommand:
    id_utilisateur: int
    code_otp: str


@dataclass(frozen=True)
class SetupTotpCommand:
    id_utilisateur: int


@dataclass(frozen=True)
class VerifyTotpCommand:
    id_utilisateur: int
    jeton: str
