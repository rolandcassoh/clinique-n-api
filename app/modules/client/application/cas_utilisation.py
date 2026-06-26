"""Cas d'utilisation du module client (customer)."""
from datetime import date

from app.modules.client.domain.entites import CustomerProfile, FamilyMember
from app.modules.client.domain.exceptions import (
    CustomerProfileNotFoundError,
    FamilyMemberAccessDeniedError,
    FamilyMemberNotFoundError,
)
from app.modules.client.domain.depots import (
    AbstractCustomerProfileRepository,
    AbstractFamilyMemberRepository,
)


class GetCustomerProfileUseCase:
    def __init__(self, profile_repo: AbstractCustomerProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(self, id_utilisateur: int) -> CustomerProfile:
        profil = await self._profile_repo.get_by_user_id(id_utilisateur)
        if profil is None:
            raise CustomerProfileNotFoundError(id_utilisateur)
        return profil


class UpdateCustomerProfileUseCase:
    def __init__(self, profile_repo: AbstractCustomerProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(
        self,
        id_utilisateur: int,
        avatar: str | None = None,
        adresse: str | None = None,
        id_ville: int | None = None,
        date_naissance: date | None = None,
        sexe: str | None = None,
        groupe_sanguin: str | None = None,
        biographie: str | None = None,
    ) -> CustomerProfile:
        mis_a_jour = await self._profile_repo.update(
            id_utilisateur=id_utilisateur,
            avatar=avatar,
            adresse=adresse,
            id_ville=id_ville,
            date_naissance=date_naissance,
            sexe=sexe,
            groupe_sanguin=groupe_sanguin,
            biographie=biographie,
        )
        if mis_a_jour is None:
            raise CustomerProfileNotFoundError(id_utilisateur)
        return mis_a_jour


class ListFamilyMembersUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(self, id_utilisateur: int) -> list[FamilyMember]:
        return await self._member_repo.list_by_user(id_utilisateur)


class CreateFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(
        self,
        id_utilisateur: int,
        nom: str,
        relation: str,
        date_naissance: date | None = None,
        sexe: str | None = None,
        groupe_sanguin: str | None = None,
        telephone: str | None = None,
    ) -> FamilyMember:
        return await self._member_repo.create(
            id_utilisateur=id_utilisateur,
            nom=nom,
            relation=relation,
            date_naissance=date_naissance,
            sexe=sexe,
            groupe_sanguin=groupe_sanguin,
            telephone=telephone,
        )


class UpdateFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(
        self,
        member_id: int,
        current_user_id: int,
        nom: str,
        relation: str,
        date_naissance: date | None = None,
        sexe: str | None = None,
        groupe_sanguin: str | None = None,
        telephone: str | None = None,
    ) -> FamilyMember:
        existant = await self._member_repo.get_by_id(member_id)
        if existant is None or existant.is_deleted:
            raise FamilyMemberNotFoundError(member_id)
        if not existant.belongs_to(current_user_id):
            raise FamilyMemberAccessDeniedError(member_id)

        mis_a_jour = await self._member_repo.update(
            member_id=member_id,
            nom=nom,
            relation=relation,
            date_naissance=date_naissance,
            sexe=sexe,
            groupe_sanguin=groupe_sanguin,
            telephone=telephone,
        )
        if mis_a_jour is None:
            raise FamilyMemberNotFoundError(member_id)
        return mis_a_jour


class DeleteFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(self, member_id: int, current_user_id: int) -> None:
        existant = await self._member_repo.get_by_id(member_id)
        if existant is None or existant.is_deleted:
            raise FamilyMemberNotFoundError(member_id)
        if not existant.belongs_to(current_user_id):
            raise FamilyMemberAccessDeniedError(member_id)
        await self._member_repo.soft_delete(member_id)
