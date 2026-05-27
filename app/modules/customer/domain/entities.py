from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class CustomerProfile:
    id: int
    user_id: int
    name: str
    email: str
    phone: str | None
    avatar: str | None
    address: str | None
    city_id: int | None
    date_of_birth: date | None
    gender: str | None
    blood_group: str | None
    bio: str | None
    created_at: datetime


@dataclass
class FamilyMember:
    id: int
    user_id: int
    name: str
    relation: str
    date_of_birth: date | None
    gender: str | None
    blood_group: str | None
    phone: str | None
    created_at: datetime
    deleted_at: datetime | None = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self, now: datetime) -> None:
        self.deleted_at = now

    def belongs_to(self, user_id: int) -> bool:
        return self.user_id == user_id
