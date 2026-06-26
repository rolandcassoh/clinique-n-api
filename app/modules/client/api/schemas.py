from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CustomerProfileSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    nom: str
    courriel: str
    telephone: str | None
    avatar: str | None
    adresse: str | None
    id_ville: int | None
    date_naissance: date | None
    sexe: str | None
    groupe_sanguin: str | None
    biographie: str | None
    created_at: datetime


class CustomerProfileUpdateSchema(BaseModel):
    avatar: str | None = None
    adresse: str | None = None
    id_ville: int | None = None
    date_naissance: date | None = None
    sexe: str | None = None
    groupe_sanguin: str | None = None
    biographie: str | None = None


class FamilyMemberSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_utilisateur: int
    nom: str
    relation: str
    date_naissance: date | None
    sexe: str | None
    groupe_sanguin: str | None
    telephone: str | None
    created_at: datetime


class FamilyMemberCreateSchema(BaseModel):
    nom: str
    relation: str
    date_naissance: date | None = None
    sexe: str | None = None
    groupe_sanguin: str | None = None
    telephone: str | None = None


class FamilyMemberUpdateSchema(BaseModel):
    nom: str
    relation: str
    date_naissance: date | None = None
    sexe: str | None = None
    groupe_sanguin: str | None = None
    telephone: str | None = None
