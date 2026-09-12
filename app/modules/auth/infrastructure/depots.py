from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entites import User, UserProfile
from app.modules.auth.domain.depots import UserRepositoryPort
from app.modules.auth.infrastructure.modeles import (
    ModelHasRoleModel,
    RoleModel,
    UserModel,
    UserProfileModel,
)


def _model_to_entity(model: UserModel, roles: list[str]) -> User:
    profile: UserProfile | None = None
    if model.profile:
        p = model.profile
        profile = UserProfile(
            id=p.id,
            id_utilisateur=p.id_utilisateur,
            avatar=p.avatar,
            adresse=p.adresse,
            id_ville=p.id_ville,
            date_naissance=p.date_naissance,
            sexe=p.sexe,
            groupe_sanguin=p.groupe_sanguin,
            biographie=p.biographie,
        )

    return User(
        id=model.id,
        nom=model.nom,
        courriel=model.courriel,
        mot_de_passe=model.mot_de_passe,
        nom_utilisateur=model.nom_utilisateur,
        telephone=model.telephone,
        est_actif=model.est_actif,
        courriel_verifie_le=model.courriel_verifie_le,
        code_otp=model.code_otp,
        secret_totp=model.secret_totp,
        totp_actif=model.totp_actif,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
        roles=roles,
        profile=profile,
    )


async def _load_roles(session: AsyncSession, id_utilisateur: int) -> list[str]:
    requete = (
        select(RoleModel.nom)
        .join(ModelHasRoleModel, ModelHasRoleModel.id_role == RoleModel.id)
        .where(
            ModelHasRoleModel.type_modele == "App\\Models\\User",
            ModelHasRoleModel.id_modele == id_utilisateur,
        )
    )
    resultat = await session.execute(requete)
    return list(resultat.scalars().all())


class SQLAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_utilisateur: int) -> User | None:
        requete = select(UserModel).where(
            UserModel.id == id_utilisateur, UserModel.deleted_at.is_(None)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        if modele is None:
            return None
        roles = await _load_roles(self._session, modele.id)
        return _model_to_entity(modele, roles)

    async def get_by_email(self, courriel: str) -> User | None:
        requete = select(UserModel).where(
            UserModel.courriel == courriel, UserModel.deleted_at.is_(None)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        if modele is None:
            return None
        roles = await _load_roles(self._session, modele.id)
        return _model_to_entity(modele, roles)

    async def get_by_username(self, nom_utilisateur: str) -> User | None:
        requete = select(UserModel).where(
            UserModel.nom_utilisateur == nom_utilisateur, UserModel.deleted_at.is_(None)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        if modele is None:
            return None
        roles = await _load_roles(self._session, modele.id)
        return _model_to_entity(modele, roles)

    async def create(
        self,
        nom: str,
        courriel: str,
        password_hash: str,
        nom_utilisateur: str | None = None,
        telephone: str | None = None,
    ) -> User:
        model = UserModel(
            nom=nom,
            courriel=courriel,
            mot_de_passe=password_hash,
            nom_utilisateur=nom_utilisateur,
            telephone=telephone,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model, [])

    async def update_otp(self, id_utilisateur: int, code_otp: str | None) -> None:
        await self._session.execute(
            update(UserModel).where(UserModel.id == id_utilisateur).values(code_otp=code_otp)
        )

    async def verify_email(self, id_utilisateur: int) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == id_utilisateur)
            .values(courriel_verifie_le=datetime.now(UTC))
        )

    async def update_totp(self, id_utilisateur: int, secret: str | None, enabled: bool) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == id_utilisateur)
            .values(secret_totp=secret, totp_actif=enabled)
        )

    async def update_password(self, id_utilisateur: int, password_hash: str) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == id_utilisateur)
            .values(mot_de_passe=password_hash)
        )

    async def update_profile(
        self,
        id_utilisateur: int,
        nom: str | None = None,
        telephone: str | None = None,
    ) -> None:
        valeurs: dict[str, str] = {}
        if nom is not None:
            valeurs["nom"] = nom
        if telephone is not None:
            valeurs["telephone"] = telephone
        if not valeurs:
            return
        await self._session.execute(
            update(UserModel).where(UserModel.id == id_utilisateur).values(**valeurs)
        )

    async def assign_role(self, id_utilisateur: int, role_name: str) -> None:
        requete_role = select(RoleModel).where(RoleModel.nom == role_name)
        resultat = await self._session.execute(requete_role)
        role = resultat.scalar_one_or_none()

        if role is None:
            role = RoleModel(nom=role_name, nom_garde="web")
            self._session.add(role)
            await self._session.flush()

        pivot = ModelHasRoleModel(
            id_role=role.id,
            type_modele="App\\Models\\User",
            id_modele=id_utilisateur,
        )
        self._session.add(pivot)
        await self._session.flush()
