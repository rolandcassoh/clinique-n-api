from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str | None = Field(default=None, min_length=3, max_length=100)
    phone: str | None = Field(default=None, max_length=30)


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshTokenSchema(BaseModel):
    refresh_token: str


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    user_id: int


class VerifyOtpSchema(BaseModel):
    user_id: int
    otp_code: str = Field(..., min_length=4, max_length=20)


class VerifyTotpSchema(BaseModel):
    token: str = Field(..., min_length=6, max_length=8)


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    avatar: str | None = None
    address: str | None = None
    city_id: int | None = None
    date_of_birth: datetime | None = None
    gender: str | None = None
    blood_group: str | None = None
    bio: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    username: str | None = None
    phone: str | None = None
    is_active: bool
    email_verified_at: datetime | None = None
    totp_enabled: bool
    roles: list[str] = []
    created_at: datetime


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    user: UserResponse | None = None


class AccessTokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TotpSetupResponse(BaseModel):
    secret: str
    qr_code: str


class MessageResponse(BaseModel):
    message: str
