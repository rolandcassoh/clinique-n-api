"""Routeur FastAPI du module client (customer) — profil et membres de la famille."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user
from app.database import get_db
from app.modules.client.api.schemas import (
    CustomerProfileSchema,
    CustomerProfileUpdateSchema,
    FamilyMemberCreateSchema,
    FamilyMemberSchema,
    FamilyMemberUpdateSchema,
)
from app.modules.client.application.cas_utilisation import (
    CreateFamilyMemberUseCase,
    DeleteFamilyMemberUseCase,
    GetCustomerProfileUseCase,
    ListFamilyMembersUseCase,
    UpdateCustomerProfileUseCase,
    UpdateFamilyMemberUseCase,
)
from app.modules.client.domain.exceptions import (
    CustomerProfileNotFoundError,
    FamilyMemberAccessDeniedError,
    FamilyMemberNotFoundError,
)
from app.modules.client.infrastructure.depots import (
    SQLCustomerProfileRepository,
    SQLFamilyMemberRepository,
)

router = APIRouter(tags=["clients"])


def _profile_repo(db: AsyncSession = Depends(get_db)) -> SQLCustomerProfileRepository:
    return SQLCustomerProfileRepository(db)


def _member_repo(db: AsyncSession = Depends(get_db)) -> SQLFamilyMemberRepository:
    return SQLFamilyMemberRepository(db)


@router.get("/clients/profil", response_model=CustomerProfileSchema)
async def get_my_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLCustomerProfileRepository = Depends(_profile_repo),
) -> CustomerProfileSchema:
    try:
        profil = await GetCustomerProfileUseCase(repo).execute(current_user["id"])
    except CustomerProfileNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return CustomerProfileSchema.model_validate(profil.__dict__)


@router.put("/clients/profil", response_model=CustomerProfileSchema)
async def update_my_profile(
    body: CustomerProfileUpdateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLCustomerProfileRepository = Depends(_profile_repo),
) -> CustomerProfileSchema:
    """Mettre à jour le profil du client connecté."""
    try:
        profil = await UpdateCustomerProfileUseCase(repo).execute(
            id_utilisateur=current_user["id"],
            avatar=body.avatar,
            adresse=body.adresse,
            id_ville=body.id_ville,
            date_naissance=body.date_naissance,
            sexe=body.sexe,
            groupe_sanguin=body.groupe_sanguin,
            biographie=body.biographie,
        )
    except CustomerProfileNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return CustomerProfileSchema.model_validate(profil.__dict__)


@router.get("/clients/membres-famille", response_model=list[FamilyMemberSchema])
async def list_family_members(
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> list[FamilyMemberSchema]:
    """Liste les membres de la famille du client connecté."""
    membres = await ListFamilyMembersUseCase(repo).execute(current_user["id"])
    return [FamilyMemberSchema.model_validate(m.__dict__) for m in membres]


@router.post(
    "/clients/membres-famille",
    response_model=FamilyMemberSchema,
    status_code=statut.HTTP_201_CREATED,
)
async def create_family_member(
    body: FamilyMemberCreateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> FamilyMemberSchema:
    """Ajouter un membre de la famille."""
    membre = await CreateFamilyMemberUseCase(repo).execute(
        id_utilisateur=current_user["id"],
        nom=body.nom,
        relation=body.relation,
        date_naissance=body.date_naissance,
        sexe=body.sexe,
        groupe_sanguin=body.groupe_sanguin,
        telephone=body.telephone,
    )
    return FamilyMemberSchema.model_validate(membre.__dict__)


@router.put("/clients/membres-famille/{member_id}", response_model=FamilyMemberSchema)
async def update_family_member(
    member_id: int,
    body: FamilyMemberUpdateSchema,
    current_user: dict[str, Any] = Depends(get_current_user),
    repo: SQLFamilyMemberRepository = Depends(_member_repo),
) -> FamilyMemberSchema:
    """Modifier un membre de la famille."""
    try:
        membre = await UpdateFamilyMemberUseCase(repo).execute(
            member_id=member_id,
            current_user_id=current_user["id"],
            nom=body.nom,
            relation=body.relation,
            date_naissance=body.date_naissance,
            sexe=body.sexe,
            groupe_sanguin=body.groupe_sanguin,
            telephone=body.telephone,
        )
    except FamilyMemberNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except FamilyMemberAccessDeniedError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=exc.message)
    return FamilyMemberSchema.model_validate(membre.__dict__)


@router.delete(
    "/clients/membres-famille/{member_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    except FamilyMemberAccessDeniedError as exc:
        raise HTTPException(status_code=statut.HTTP_403_FORBIDDEN, detail=exc.message)
