from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProfile:
    id: int
    user_id: int
    avatar: str | None = None
    address: str | None = None
    city_id: int | None = None
    date_of_birth: datetime | None = None
    gender: str | None = None
    blood_group: str | None = None
    bio: str | None = None


@dataclass
class User:
    id: int
    name: str
    email: str
    password: str
    username: str | None = None
    phone: str | None = None
    is_active: bool = True
    email_verified_at: datetime | None = None
    otp_code: str | None = None
    totp_secret: str | None = None
    totp_enabled: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
    roles: list[str] = field(default_factory=list)
    profile: UserProfile | None = None

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return any(self.has_role(r) for r in roles)
