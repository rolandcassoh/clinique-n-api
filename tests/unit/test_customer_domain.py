"""Tests unitaires — domaine Customer (logique pure, sans I/O)."""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.modules.customer.application.use_cases import (
    CreateFamilyMemberUseCase,
    DeleteFamilyMemberUseCase,
    GetCustomerProfileUseCase,
    UpdateCustomerProfileUseCase,
    UpdateFamilyMemberUseCase,
)
from app.modules.customer.domain.entities import CustomerProfile, FamilyMember
from app.modules.customer.domain.exceptions import (
    CustomerProfileNotFoundError,
    FamilyMemberAccessDeniedError,
    FamilyMemberNotFoundError,
)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_profile(user_id: int = 1) -> CustomerProfile:
    return CustomerProfile(
        id=user_id,
        user_id=user_id,
        name="Alice",
        email="alice@clinique.app",
        phone="+33600000000",
        avatar=None,
        address="1 rue de la Paix",
        city_id=1,
        date_of_birth=date(1990, 5, 15),
        gender="female",
        blood_group="A+",
        bio="Patiente fidèle",
        created_at=datetime.now(timezone.utc),
    )


def _make_member(
    id: int = 10,
    user_id: int = 1,
    deleted_at: datetime | None = None,
) -> FamilyMember:
    return FamilyMember(
        id=id,
        user_id=user_id,
        name="Bob",
        relation="fils",
        date_of_birth=date(2015, 3, 10),
        gender="male",
        blood_group="O+",
        phone=None,
        created_at=datetime.now(timezone.utc),
        deleted_at=deleted_at,
    )


# ── FamilyMember entity ───────────────────────────────────────────────────────


class TestFamilyMemberEntity:
    def test_creation_valide(self) -> None:
        member = _make_member()
        assert member.id == 10
        assert member.user_id == 1
        assert not member.is_deleted

    def test_soft_delete(self) -> None:
        member = _make_member()
        now = datetime.now(timezone.utc)
        member.soft_delete(now)
        assert member.is_deleted
        assert member.deleted_at == now

    def test_appartenance_user_correct(self) -> None:
        member = _make_member(user_id=1)
        assert member.belongs_to(1) is True
        assert member.belongs_to(2) is False

    def test_member_supprime_est_deleted(self) -> None:
        deleted_at = datetime.now(timezone.utc)
        member = _make_member(deleted_at=deleted_at)
        assert member.is_deleted is True


# ── CustomerProfile modification partielle ────────────────────────────────────


class TestCustomerProfileUpdate:
    @pytest.mark.asyncio
    async def test_update_partiel_avatar_uniquement(self) -> None:
        repo = AsyncMock()
        profile = _make_profile()
        updated_profile = CustomerProfile(
            **{**profile.__dict__, "avatar": "nouveau_avatar.jpg"}
        )
        repo.update.return_value = updated_profile

        uc = UpdateCustomerProfileUseCase(repo)
        result = await uc.execute(user_id=1, avatar="nouveau_avatar.jpg")

        repo.update.assert_awaited_once()
        assert result.avatar == "nouveau_avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_raises_not_found_si_user_inexistant(self) -> None:
        repo = AsyncMock()
        repo.update.return_value = None

        uc = UpdateCustomerProfileUseCase(repo)
        with pytest.raises(CustomerProfileNotFoundError):
            await uc.execute(user_id=999)

    @pytest.mark.asyncio
    async def test_get_profile_raises_not_found_si_absent(self) -> None:
        repo = AsyncMock()
        repo.get_by_user_id.return_value = None

        uc = GetCustomerProfileUseCase(repo)
        with pytest.raises(CustomerProfileNotFoundError):
            await uc.execute(user_id=42)

    @pytest.mark.asyncio
    async def test_get_profile_retourne_profil_existant(self) -> None:
        repo = AsyncMock()
        profile = _make_profile(user_id=5)
        repo.get_by_user_id.return_value = profile

        uc = GetCustomerProfileUseCase(repo)
        result = await uc.execute(user_id=5)

        assert result.user_id == 5
        assert result.name == "Alice"


# ── FamilyMember use cases ───────────────────────────────────────────────────


class TestFamilyMemberUseCases:
    @pytest.mark.asyncio
    async def test_create_member_succes(self) -> None:
        repo = AsyncMock()
        member = _make_member()
        repo.create.return_value = member

        uc = CreateFamilyMemberUseCase(repo)
        result = await uc.execute(
            user_id=1, name="Bob", relation="fils", date_of_birth=date(2015, 3, 10)
        )

        repo.create.assert_awaited_once()
        assert result.name == "Bob"

    @pytest.mark.asyncio
    async def test_update_member_autre_user_leve_403(self) -> None:
        repo = AsyncMock()
        # Member appartient à user_id=1
        repo.get_by_id.return_value = _make_member(user_id=1)

        uc = UpdateFamilyMemberUseCase(repo)
        with pytest.raises(FamilyMemberAccessDeniedError):
            await uc.execute(
                member_id=10,
                current_user_id=2,  # autre user
                name="Bob",
                relation="fils",
            )

    @pytest.mark.asyncio
    async def test_update_member_inexistant_leve_404(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = None

        uc = UpdateFamilyMemberUseCase(repo)
        with pytest.raises(FamilyMemberNotFoundError):
            await uc.execute(
                member_id=999,
                current_user_id=1,
                name="X",
                relation="parent",
            )

    @pytest.mark.asyncio
    async def test_update_member_supprime_leve_404(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = _make_member(deleted_at=datetime.now(timezone.utc))

        uc = UpdateFamilyMemberUseCase(repo)
        with pytest.raises(FamilyMemberNotFoundError):
            await uc.execute(
                member_id=10,
                current_user_id=1,
                name="X",
                relation="parent",
            )

    @pytest.mark.asyncio
    async def test_delete_member_autre_user_leve_403(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = _make_member(user_id=1)

        uc = DeleteFamilyMemberUseCase(repo)
        with pytest.raises(FamilyMemberAccessDeniedError):
            await uc.execute(member_id=10, current_user_id=2)

    @pytest.mark.asyncio
    async def test_delete_member_inexistant_leve_404(self) -> None:
        repo = AsyncMock()
        repo.get_by_id.return_value = None

        uc = DeleteFamilyMemberUseCase(repo)
        with pytest.raises(FamilyMemberNotFoundError):
            await uc.execute(member_id=999, current_user_id=1)
