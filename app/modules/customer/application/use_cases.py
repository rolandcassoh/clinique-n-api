from datetime import date

from app.modules.customer.domain.entities import CustomerProfile, FamilyMember
from app.modules.customer.domain.exceptions import (
    CustomerProfileNotFoundError,
    FamilyMemberAccessDeniedError,
    FamilyMemberNotFoundError,
)
from app.modules.customer.domain.repositories import (
    AbstractCustomerProfileRepository,
    AbstractFamilyMemberRepository,
)


class GetCustomerProfileUseCase:
    def __init__(self, profile_repo: AbstractCustomerProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(self, user_id: int) -> CustomerProfile:
        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            raise CustomerProfileNotFoundError(user_id)
        return profile


class UpdateCustomerProfileUseCase:
    def __init__(self, profile_repo: AbstractCustomerProfileRepository) -> None:
        self._profile_repo = profile_repo

    async def execute(
        self,
        user_id: int,
        avatar: str | None = None,
        address: str | None = None,
        city_id: int | None = None,
        date_of_birth: date | None = None,
        gender: str | None = None,
        blood_group: str | None = None,
        bio: str | None = None,
    ) -> CustomerProfile:
        updated = await self._profile_repo.update(
            user_id=user_id,
            avatar=avatar,
            address=address,
            city_id=city_id,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            bio=bio,
        )
        if updated is None:
            raise CustomerProfileNotFoundError(user_id)
        return updated


class ListFamilyMembersUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(self, user_id: int) -> list[FamilyMember]:
        return await self._member_repo.list_by_user(user_id)


class CreateFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(
        self,
        user_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None = None,
        gender: str | None = None,
        blood_group: str | None = None,
        phone: str | None = None,
    ) -> FamilyMember:
        return await self._member_repo.create(
            user_id=user_id,
            name=name,
            relation=relation,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            phone=phone,
        )


class UpdateFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(
        self,
        member_id: int,
        current_user_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None = None,
        gender: str | None = None,
        blood_group: str | None = None,
        phone: str | None = None,
    ) -> FamilyMember:
        existing = await self._member_repo.get_by_id(member_id)
        if existing is None or existing.is_deleted:
            raise FamilyMemberNotFoundError(member_id)
        if not existing.belongs_to(current_user_id):
            raise FamilyMemberAccessDeniedError(member_id)

        updated = await self._member_repo.update(
            member_id=member_id,
            name=name,
            relation=relation,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            phone=phone,
        )
        if updated is None:
            raise FamilyMemberNotFoundError(member_id)
        return updated


class DeleteFamilyMemberUseCase:
    def __init__(self, member_repo: AbstractFamilyMemberRepository) -> None:
        self._member_repo = member_repo

    async def execute(self, member_id: int, current_user_id: int) -> None:
        existing = await self._member_repo.get_by_id(member_id)
        if existing is None or existing.is_deleted:
            raise FamilyMemberNotFoundError(member_id)
        if not existing.belongs_to(current_user_id):
            raise FamilyMemberAccessDeniedError(member_id)
        await self._member_repo.soft_delete(member_id)
