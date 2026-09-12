from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterSchema(BaseModel):
    nom: str = Field(..., min_length=2, max_length=255)
    courriel: EmailStr
    mot_de_passe: str = Field(..., min_length=8, max_length=128)
    nom_utilisateur: str | None = Field(default=None, min_length=3, max_length=100)
    telephone: str | None = Field(default=None, max_length=30)


class LoginSchema(BaseModel):
    courriel: EmailStr
    mot_de_passe: str = Field(..., min_length=1)


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class ForgotPasswordSchema(BaseModel):
    courriel: EmailStr


class ResetPasswordSchema(BaseModel):
    jeton: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    id_utilisateur: int


class UpdateProfileSchema(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=255)
    telephone: str | None = Field(default=None, max_length=30)


class ChangePasswordSchema(BaseModel):
    mot_de_passe_actuel: str = Field(..., min_length=1)
    nouveau_mot_de_passe: str = Field(..., min_length=8, max_length=128)


class VerifyOtpSchema(BaseModel):
    id_utilisateur: int
    code_otp: str = Field(..., min_length=4, max_length=20)


class VerifyTotpSchema(BaseModel):
    jeton: str = Field(..., min_length=6, max_length=8)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    avatar: str | None = None
    adresse: str | None = None
    id_ville: int | None = None
    date_naissance: datetime | None = None
    sexe: str | None = None
    groupe_sanguin: str | None = None
    biographie: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    courriel: str
    nom_utilisateur: str | None = None
    telephone: str | None = None
    est_actif: bool
    courriel_verifie_le: datetime | None = None
    totp_actif: bool
    roles: list[str] = []
    created_at: datetime


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    type_jeton: str = "Bearer"
    user: UserResponse | None = None


class AccessTokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    type_jeton: str = "Bearer"


class TotpSetupResponse(BaseModel):
    secret: str
    qr_code: str


class MessageResponse(BaseModel):
    message: str
