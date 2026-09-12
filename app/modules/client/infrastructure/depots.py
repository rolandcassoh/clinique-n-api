"""Implémentations SQLAlchemy asynchrones des repositories client (customer)."""
from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.modeles import UserModel, UserProfileModel
from app.modules.client.domain.entites import CustomerProfile, FamilyMember
from app.modules.client.domain.depots import (
    AbstractCustomerProfileRepository,
    AbstractFamilyMemberRepository,
)
from app.modules.client.infrastructure.modeles import OtherPatientModel


def _profile_to_entity(user: UserModel, profile: UserProfileModel | None) -> CustomerProfile:
    dob = None
    if profile and profile.date_naissance:
        dob = profile.date_naissance.date() if hasattr(profile.date_naissance, "date") else profile.date_naissance
    return CustomerProfile(
        id=user.id,
        id_utilisateur=user.id,
        nom=user.nom,
        courriel=user.courriel,
        telephone=user.telephone,
        avatar=profile.avatar if profile else None,
        adresse=profile.adresse if profile else None,
        id_ville=profile.id_ville if profile else None,
        date_naissance=dob,
        sexe=profile.sexe if profile else None,
        groupe_sanguin=profile.groupe_sanguin if profile else None,
        biographie=profile.biographie if profile else None,
        created_at=user.created_at,
    )


def _member_to_entity(m: OtherPatientModel) -> FamilyMember:
    return FamilyMember(
        id=m.id,
        id_utilisateur=m.id_utilisateur,
        nom=m.nom,
        relation=m.relation,
        date_naissance=m.date_naissance,
        sexe=m.sexe,
        groupe_sanguin=m.groupe_sanguin,
        telephone=m.telephone,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


class SQLCustomerProfileRepository(AbstractCustomerProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, id_utilisateur: int) -> CustomerProfile | None:
        requete = select(UserModel).where(
            UserModel.id == id_utilisateur,
            UserModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        utilisateur = resultat.scalar_one_or_none()
        if utilisateur is None:
            return None
        return _profile_to_entity(utilisateur, utilisateur.profile)

    async def update(
        self,
        id_utilisateur: int,
        avatar: str | None = None,
        adresse: str | None = None,
        id_ville: int | None = None,
        date_naissance: date | None = None,
        sexe: str | None = None,
        groupe_sanguin: str | None = None,
        biographie: str | None = None,
    ) -> CustomerProfile | None:
        # Récupère l'utilisateur avec son profil
        requete = select(UserModel).where(
            UserModel.id == id_utilisateur,
            UserModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        utilisateur = resultat.scalar_one_or_none()
        if utilisateur is None:
            return None

        # Met à jour ou crée le profil associé
        if utilisateur.profile is None:
            profil = UserProfileModel(id_utilisateur=id_utilisateur)
            self._session.add(profil)
        else:
            profil = utilisateur.profile

        if avatar is not None:
            profil.avatar = avatar
        if adresse is not None:
            profil.adresse = adresse
        if id_ville is not None:
            profil.id_ville = id_ville
        if date_naissance is not None:
            profil.date_naissance = datetime(
                date_naissance.year, date_naissance.month, date_naissance.day
            )
        if sexe is not None:
            profil.sexe = sexe
        if groupe_sanguin is not None:
            profil.groupe_sanguin = groupe_sanguin
        if biographie is not None:
            profil.biographie = biographie

        await self._session.flush()
        await self._session.refresh(utilisateur)
        return _profile_to_entity(utilisateur, utilisateur.profile)


class SQLFamilyMemberRepository(AbstractFamilyMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(self, id_utilisateur: int) -> list[FamilyMember]:
        requete = select(OtherPatientModel).where(
            OtherPatientModel.id_utilisateur == id_utilisateur,
            OtherPatientModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        return [_member_to_entity(modele) for modele in resultat.scalars().all()]

    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        requete = select(OtherPatientModel).where(OtherPatientModel.id == member_id)
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _member_to_entity(modele) if modele else None

    async def create(
        self,
        id_utilisateur: int,
        nom: str,
        relation: str,
        date_naissance: date | None,
        sexe: str | None,
        groupe_sanguin: str | None,
        telephone: str | None,
    ) -> FamilyMember:
        modele = OtherPatientModel(
            id_utilisateur=id_utilisateur,
            nom=nom,
            relation=relation,
            date_naissance=date_naissance,
            sexe=sexe,
            groupe_sanguin=groupe_sanguin,
            telephone=telephone,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _member_to_entity(modele)

    async def update(
        self,
        member_id: int,
        nom: str,
        relation: str,
        date_naissance: date | None,
        sexe: str | None,
        groupe_sanguin: str | None,
        telephone: str | None,
    ) -> FamilyMember | None:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne.
        requete = (
            update(OtherPatientModel)
            .where(
                OtherPatientModel.id == member_id,
                OtherPatientModel.deleted_at.is_(None),
            )
            .values(
                nom=nom,
                relation=relation,
                date_naissance=date_naissance,
                sexe=sexe,
                groupe_sanguin=groupe_sanguin,
                telephone=telephone,
            )
        )
        resultat = await self._session.execute(requete)
        if resultat.rowcount == 0:
            return None
        modele = (
            await self._session.execute(
                select(OtherPatientModel).where(OtherPatientModel.id == member_id)
            )
        ).scalar_one_or_none()
        return _member_to_entity(modele) if modele else None

    async def soft_delete(self, member_id: int) -> bool:
        requete = (
            update(OtherPatientModel)
            .where(
                OtherPatientModel.id == member_id,
                OtherPatientModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        resultat = await self._session.execute(requete)
        return resultat.rowcount > 0
