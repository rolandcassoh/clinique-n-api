from datetime import date, datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.infrastructure.models import UserModel, UserProfileModel
from app.modules.customer.domain.entities import CustomerProfile, FamilyMember
from app.modules.customer.domain.repositories import (
    AbstractCustomerProfileRepository,
    AbstractFamilyMemberRepository,
)
from app.modules.customer.infrastructure.models import OtherPatientModel


def _profile_to_entity(user: UserModel, profile: UserProfileModel | None) -> CustomerProfile:
    dob = None
    if profile and profile.date_of_birth:
        dob = profile.date_of_birth.date() if hasattr(profile.date_of_birth, "date") else profile.date_of_birth
    return CustomerProfile(
        id=user.id,
        user_id=user.id,
        name=user.name,
        email=user.email,
        phone=user.phone,
        avatar=profile.avatar if profile else None,
        address=profile.address if profile else None,
        city_id=profile.city_id if profile else None,
        date_of_birth=dob,
        gender=profile.gender if profile else None,
        blood_group=profile.blood_group if profile else None,
        bio=profile.bio if profile else None,
        created_at=user.created_at,
    )


def _member_to_entity(m: OtherPatientModel) -> FamilyMember:
    return FamilyMember(
        id=m.id,
        user_id=m.user_id,
        name=m.name,
        relation=m.relation,
        date_of_birth=m.date_of_birth,
        gender=m.gender,
        blood_group=m.blood_group,
        phone=m.phone,
        created_at=m.created_at,
        deleted_at=m.deleted_at,
    )


class SQLCustomerProfileRepository(AbstractCustomerProfileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: int) -> CustomerProfile | None:
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return None
        return _profile_to_entity(user, user.profile)

    async def update(
        self,
        user_id: int,
        avatar: str | None = None,
        address: str | None = None,
        city_id: int | None = None,
        date_of_birth: date | None = None,
        gender: str | None = None,
        blood_group: str | None = None,
        bio: str | None = None,
    ) -> CustomerProfile | None:
        # Récupère le user avec son profil
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            return None

        # Met à jour ou crée le profil
        if user.profile is None:
            profile = UserProfileModel(user_id=user_id)
            self._session.add(profile)
        else:
            profile = user.profile

        if avatar is not None:
            profile.avatar = avatar
        if address is not None:
            profile.address = address
        if city_id is not None:
            profile.city_id = city_id
        if date_of_birth is not None:
            profile.date_of_birth = datetime(
                date_of_birth.year, date_of_birth.month, date_of_birth.day
            )
        if gender is not None:
            profile.gender = gender
        if blood_group is not None:
            profile.blood_group = blood_group
        if bio is not None:
            profile.bio = bio

        await self._session.flush()
        await self._session.refresh(user)
        return _profile_to_entity(user, user.profile)


class SQLFamilyMemberRepository(AbstractFamilyMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(self, user_id: int) -> list[FamilyMember]:
        stmt = select(OtherPatientModel).where(
            OtherPatientModel.user_id == user_id,
            OtherPatientModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return [_member_to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, member_id: int) -> FamilyMember | None:
        stmt = select(OtherPatientModel).where(OtherPatientModel.id == member_id)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _member_to_entity(m) if m else None

    async def create(
        self,
        user_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None,
        gender: str | None,
        blood_group: str | None,
        phone: str | None,
    ) -> FamilyMember:
        m = OtherPatientModel(
            user_id=user_id,
            name=name,
            relation=relation,
            date_of_birth=date_of_birth,
            gender=gender,
            blood_group=blood_group,
            phone=phone,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _member_to_entity(m)

    async def update(
        self,
        member_id: int,
        name: str,
        relation: str,
        date_of_birth: date | None,
        gender: str | None,
        blood_group: str | None,
        phone: str | None,
    ) -> FamilyMember | None:
        stmt = (
            update(OtherPatientModel)
            .where(
                OtherPatientModel.id == member_id,
                OtherPatientModel.deleted_at.is_(None),
            )
            .values(
                name=name,
                relation=relation,
                date_of_birth=date_of_birth,
                gender=gender,
                blood_group=blood_group,
                phone=phone,
            )
            .returning(OtherPatientModel)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return _member_to_entity(m) if m else None

    async def soft_delete(self, member_id: int) -> bool:
        stmt = (
            update(OtherPatientModel)
            .where(
                OtherPatientModel.id == member_id,
                OtherPatientModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0
