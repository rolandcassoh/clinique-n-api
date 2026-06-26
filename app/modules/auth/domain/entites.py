from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserProfile:
    id: int
    id_utilisateur: int
    avatar: str | None = None
    adresse: str | None = None
    id_ville: int | None = None
    date_naissance: datetime | None = None
    sexe: str | None = None
    groupe_sanguin: str | None = None
    biographie: str | None = None


@dataclass
class User:
    id: int
    nom: str
    courriel: str
    mot_de_passe: str
    nom_utilisateur: str | None = None
    telephone: str | None = None
    est_actif: bool = True
    courriel_verifie_le: datetime | None = None
    code_otp: str | None = None
    secret_totp: str | None = None
    totp_actif: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: datetime | None = None
    roles: list[str] = field(default_factory=list)
    profile: UserProfile | None = None

    @property
    def is_email_verified(self) -> bool:
        return self.courriel_verifie_le is not None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def has_any_role(self, *roles: str) -> bool:
        return any(self.has_role(r) for r in roles)
