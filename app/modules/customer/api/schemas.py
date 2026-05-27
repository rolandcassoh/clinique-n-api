from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CustomerProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class CustomerProfileUpdateSchema(BaseModel):
    avatar: str | None = None
    address: str | None = None
    city_id: int | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    bio: str | None = None


class FamilyMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    relation: str
    date_of_birth: date | None
    gender: str | None
    blood_group: str | None
    phone: str | None
    created_at: datetime


class FamilyMemberCreateSchema(BaseModel):
    name: str
    relation: str
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None


class FamilyMemberUpdateSchema(BaseModel):
    name: str
    relation: str
    date_of_birth: date | None = None
    gender: str | None = None
    blood_group: str | None = None
    phone: str | None = None
