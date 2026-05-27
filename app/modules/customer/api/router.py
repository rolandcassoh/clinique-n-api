from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.database import get_db
from app.modules.customer.api.schemas import (
    CustomerProfileSchema,
    CustomerProfileUpdateSchema,
    FamilyMemberCreateSchema,
    FamilyMemberSchema,
    FamilyMemberUpdateSchema,
)
from app.modules.customer.application.use_cases import (
    CreateFamilyMemberUseCase,
    DeleteFamilyMemberUseCase,
    GetCustomerProfileUseCase,
    ListFamilyMembersUseCase,
    UpdateCustomerProfileUseCase,
    UpdateFamilyMemberUseCase,
)
from app.modules.customer.domain.exceptions import (
    CustomerProfileNotFoundError,
    FamilyMemberAccessDeniedError,
    FamilyMemberNotFoundError,
)
from app.modules.customer.infrastructure.repositories import (
    SQLCustomerProfileRepository,
    SQLFamilyMemberRepository,
)

router = APIRouter(tags=["customers"])


def _profile_repo(db: AsyncSession = Depends(get_db)) -> SQLCustomerProfileRepository:
    return SQLCustomerProfileRepository(db)


def _member_repo(db: AsyncSession = Depends(get_db)) -> SQLFamilyMemberRepository:
    return SQLFamilyMemberRepository(db)


@router.get("/customers/profile", response_model=CustomerProfileSchema)
async def get_my_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLCustomerProfileRepository = Depends(_profile_repo),
) -> CustomerProfileSchema:
    try:
        profile = await GetCustomerProfileUseCase(repo).execute(current_user["id"])
    except CustomerProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return CustomerProfileSchema.model_validate(profile.__dict__)


@router.put("/customers/profile", response_model=CustomerProfileSchema)
async def update_my_profile(
    body: CustomerProfileUpdateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLCustomerProfileRepository = Depends(_profile_repo),
) -> CustomerProfileSchema:
    try:
        profile = await UpdateCustomerProfileUseCase(repo).execute(
            user_id=current_user["id"],
            avatar=body.avatar,
            address=body.address,
            city_id=body.city_id,
            date_of_birth=body.date_of_birth,
            gender=body.gender,
            blood_group=body.blood_group,
            bio=body.bio,
        )
    except CustomerProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return CustomerProfileSchema.model_validate(profile.__dict__)


@router.get("/customers/family-members", response_model=list[FamilyMemberSchema])
async def list_family_members(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> list[FamilyMemberSchema]:
    members = await ListFamilyMembersUseCase(repo).execute(current_user["id"])
    return [FamilyMemberSchema.model_validate(m.__dict__) for m in members]


@router.post(
    "/customers/family-members",
    response_model=FamilyMemberSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_family_member(
    body: FamilyMemberCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> FamilyMemberSchema:
    member = await CreateFamilyMemberUseCase(repo).execute(
        user_id=current_user["id"],
        name=body.name,
        relation=body.relation,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        blood_group=body.blood_group,
        phone=body.phone,
    )
    return FamilyMemberSchema.model_validate(member.__dict__)


@router.put("/customers/family-members/{member_id}", response_model=FamilyMemberSchema)
async def update_family_member(
    member_id: int,
    body: FamilyMemberUpdateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> FamilyMemberSchema:
    try:
        member = await UpdateFamilyMemberUseCase(repo).execute(
            member_id=member_id,
            current_user_id=current_user["id"],
            name=body.name,
            relation=body.relation,
            date_of_birth=body.date_of_birth,
            gender=body.gender,
            blood_group=body.blood_group,
            phone=body.phone,
        )
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except FamilyMemberAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
    return FamilyMemberSchema.model_validate(member.__dict__)


@router.delete(
    "/customers/family-members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_family_member(
    member_id: int,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> None:
    try:
        await DeleteFamilyMemberUseCase(repo).execute(
            member_id=member_id,
            current_user_id=current_user["id"],
        )
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    except FamilyMemberAccessDeniedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=exc.message)
