from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.models.base import BaseModel
from app.database import Base


class RoleModel(Base):
    # Table BD : rôles
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    nom_garde: Mapped[str] = mapped_column(String(255), nullable=False, default="web")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("nom", "nom_garde", name="uq_roles_name_guard"),)


class ModelHasRoleModel(Base):
    # Table BD : modèle_a_rôles
    __tablename__ = "modele_a_roles"

    id_role: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    type_modele: Mapped[str] = mapped_column(String(255), primary_key=True)
    id_modele: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)


class UserModel(BaseModel):
    # Table BD : utilisateurs
    __tablename__ = "utilisateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(255), nullable=False)
    courriel: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    mot_de_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    nom_utilisateur: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    telephone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    est_actif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    courriel_verifie_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    code_otp: Mapped[str | None] = mapped_column(String(20), nullable=True)
    secret_totp: Mapped[str | None] = mapped_column(String(255), nullable=True)
    totp_actif: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped["UserProfileModel | None"] = relationship(
        "UserProfileModel", back_populates="user", uselist=False, lazy="selectin"
    )
    tokens: Mapped[list["PersonalAccessTokenModel"]] = relationship(
        "PersonalAccessTokenModel", back_populates="user", cascade="all, delete-orphan"
    )


class UserProfileModel(Base):
    # Table BD : profils_utilisateurs
    __tablename__ = "profils_utilisateurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), unique=True, nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    adresse: Mapped[str | None] = mapped_column(Text, nullable=True)
    id_ville: Mapped[int | None] = mapped_column(Integer, nullable=True)
    date_naissance: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    sexe: Mapped[str | None] = mapped_column(
        Enum("male", "female", "other", name="gender_enum"), nullable=True)
    groupe_sanguin: Mapped[str | None] = mapped_column(String(10), nullable=True)
    biographie: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="profile")


class PersonalAccessTokenModel(Base):
    # Table BD : jetons_accès_personnels
    __tablename__ = "jetons_acces_personnels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_utilisateur: Mapped[int] = mapped_column(
        Integer, ForeignKey("utilisateurs.id", ondelete="CASCADE"), nullable=False, index=True)
    jeton: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    type_jeton: Mapped[str] = mapped_column(String(50), default="access", nullable=False)
    expire_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    derniere_utilisation_le: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    est_revoque: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="tokens")
