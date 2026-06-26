"""Routeur FastAPI du module portefeuille."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.portefeuille.api.schemas import (
    PayAppointmentRequest,
    TopUpRequest,
    WalletHistorySchema,
    WalletSchema,
)
from app.modules.portefeuille.application.cas_utilisation import (
    AdminGetWalletUseCase,
    AdminListWalletsUseCase,
    GetMyWalletUseCase,
    GetWalletHistoryUseCase,
    PayAppointmentWithWalletUseCase,
    TopUpWalletUseCase,
)
from app.modules.portefeuille.domain.exceptions import InsufficientFundsError, WalletNotFoundError
from app.modules.portefeuille.infrastructure.depots import SQLAlchemyWalletRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Portefeuille"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _wallet_repo(db: DbDep) -> SQLAlchemyWalletRepository:
    return SQLAlchemyWalletRepository(db)


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

@router.get("/portefeuille", response_model=WalletSchema)
async def get_my_wallet(
    current_user: CurrentUserDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = GetMyWalletUseCase(wallet_repo)
    wallet = await uc.execute(current_user["id"])
    return WalletSchema.model_validate(wallet)


@router.get("/portefeuille/historique", response_model=Page[WalletHistorySchema])
async def get_wallet_history(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> Page[WalletHistorySchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = GetWalletHistoryUseCase(wallet_repo)
    return await uc.execute(current_user["id"], params)  # type: ignore[return-valeur]


@router.post("/portefeuille/crediter", response_model=WalletSchema, status_code=statut.HTTP_200_OK)
async def topup_wallet(
    payload: TopUpRequest,
    current_user: CurrentUserDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = TopUpWalletUseCase(wallet_repo)
    wallet = await uc.execute(
        id_utilisateur=current_user["id"],
        montant=payload.montant,
        passerelle=payload.passerelle,
        reference=payload.reference,
    )
    return WalletSchema.model_validate(wallet)


@router.post(
    "/portefeuille/payer-rendez-vous",
    response_model=WalletSchema,
    status_code=statut.HTTP_200_OK,
)
async def pay_appointment_with_wallet(
    payload: PayAppointmentRequest,
    current_user: CurrentUserDep,
    db: DbDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = PayAppointmentWithWalletUseCase(wallet_repo, db)
    try:
        wallet = await uc.execute(
            id_utilisateur=current_user["id"],
            id_rendez_vous=payload.id_rendez_vous,
            montant=payload.montant,
        )
    except WalletNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=statut.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return WalletSchema.model_validate(wallet)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/portefeuilles", response_model=Page[WalletSchema])
async def admin_list_wallets(
    current_user: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> Page[WalletSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListWalletsUseCase(wallet_repo)
    return await uc.execute(params)  # type: ignore[return-valeur]


@router.get("/admin/portefeuilles/{id_utilisateur}", response_model=WalletSchema)
async def admin_get_wallet(
    id_utilisateur: int,
    current_user: AdminDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = AdminGetWalletUseCase(wallet_repo)
    try:
        wallet = await uc.execute(id_utilisateur)
    except WalletNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WalletSchema.model_validate(wallet)
