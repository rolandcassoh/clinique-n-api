from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.entities import User, UserProfile
from app.modules.auth.domain.repositories import UserRepositoryPort
from app.modules.auth.infrastructure.models import (
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
            user_id=p.user_id,
            avatar=p.avatar,
            address=p.address,
            city_id=p.city_id,
            date_of_birth=p.date_of_birth,
            gender=p.gender,
            blood_group=p.blood_group,
            bio=p.bio,
        )

    return User(
        id=model.id,
        name=model.name,
        email=model.email,
        password=model.password,
        username=model.username,
        phone=model.phone,
        is_active=model.is_active,
        email_verified_at=model.email_verified_at,
        otp_code=model.otp_code,
        totp_secret=model.totp_secret,
        totp_enabled=model.totp_enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
        roles=roles,
        profile=profile,
    )


async def _load_roles(session: AsyncSession, user_id: int) -> list[str]:
    stmt = (
        select(RoleModel.name)
        .join(ModelHasRoleModel, ModelHasRoleModel.role_id == RoleModel.id)
        .where(
            ModelHasRoleModel.model_type == "App\\Models\\User",
            ModelHasRoleModel.model_id == user_id,
        )
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


class SQLAlchemyUserRepository(UserRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        stmt = select(UserModel).where(
            UserModel.id == user_id, UserModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        roles = await _load_roles(self._session, model.id)
        return _model_to_entity(model, roles)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == email, UserModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        roles = await _load_roles(self._session, model.id)
        return _model_to_entity(model, roles)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(
            UserModel.username == username, UserModel.deleted_at.is_(None)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        roles = await _load_roles(self._session, model.id)
        return _model_to_entity(model, roles)

    async def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        username: str | None = None,
        phone: str | None = None,
    ) -> User:
        model = UserModel(
            name=name,
            email=email,
            password=password_hash,
            username=username,
            phone=phone,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _model_to_entity(model, [])

    async def update_otp(self, user_id: int, otp_code: str | None) -> None:
        await self._session.execute(
            update(UserModel).where(UserModel.id == user_id).values(otp_code=otp_code)
        )

    async def verify_email(self, user_id: int) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(email_verified_at=datetime.now(UTC))
        )

    async def update_totp(self, user_id: int, secret: str | None, enabled: bool) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(totp_secret=secret, totp_enabled=enabled)
        )

    async def update_password(self, user_id: int, password_hash: str) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(password=password_hash)
        )

    async def assign_role(self, user_id: int, role_name: str) -> None:
        role_stmt = select(RoleModel).where(RoleModel.name == role_name)
        result = await self._session.execute(role_stmt)
        role = result.scalar_one_or_none()

        if role is None:
            role = RoleModel(name=role_name, guard_name="web")
            self._session.add(role)
            await self._session.flush()

        pivot = ModelHasRoleModel(
            role_id=role.id,
            model_type="App\\Models\\User",
            model_id=user_id,
        )
        self._session.add(pivot)
        await self._session.flush()
