"""Router FastAPI du module wallet."""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import get_current_user, require_role
from app.database import get_db
from app.modules.wallet.api.schemas import (
    PayAppointmentRequest,
    TopUpRequest,
    WalletHistorySchema,
    WalletSchema,
)
from app.modules.wallet.application.use_cases import (
    AdminGetWalletUseCase,
    AdminListWalletsUseCase,
    GetMyWalletUseCase,
    GetWalletHistoryUseCase,
    PayAppointmentWithWalletUseCase,
    TopUpWalletUseCase,
)
from app.modules.wallet.domain.exceptions import InsufficientFundsError, WalletNotFoundError
from app.modules.wallet.infrastructure.repositories import SQLAlchemyWalletRepository
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Wallet"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[dict[str, Any], Depends(get_current_user)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _wallet_repo(db: DbDep) -> SQLAlchemyWalletRepository:
    return SQLAlchemyWalletRepository(db)


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

@router.get("/wallet", response_model=WalletSchema)
async def get_my_wallet(
    current_user: CurrentUserDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = GetMyWalletUseCase(wallet_repo)
    wallet = await uc.execute(current_user["id"])
    return WalletSchema.model_validate(wallet)


@router.get("/wallet/history", response_model=Page[WalletHistorySchema])
async def get_wallet_history(
    current_user: CurrentUserDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> Page[WalletHistorySchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = GetWalletHistoryUseCase(wallet_repo)
    return await uc.execute(current_user["id"], params)  # type: ignore[return-value]


@router.post("/wallet/topup", response_model=WalletSchema, status_code=status.HTTP_200_OK)
async def topup_wallet(
    payload: TopUpRequest,
    current_user: CurrentUserDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = TopUpWalletUseCase(wallet_repo)
    wallet = await uc.execute(
        user_id=current_user["id"],
        amount=payload.amount,
        gateway=payload.gateway,
        reference=payload.reference,
    )
    return WalletSchema.model_validate(wallet)


@router.post(
    "/wallet/pay-appointment",
    response_model=WalletSchema,
    status_code=status.HTTP_200_OK,
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
            user_id=current_user["id"],
            appointment_id=payload.appointment_id,
            amount=payload.amount,
        )
    except WalletNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InsufficientFundsError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    return WalletSchema.model_validate(wallet)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

@router.get("/admin/wallets", response_model=Page[WalletSchema])
async def admin_list_wallets(
    current_user: AdminDep,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> Page[WalletSchema]:
    params = PaginationParams(page=page, per_page=per_page)
    uc = AdminListWalletsUseCase(wallet_repo)
    return await uc.execute(params)  # type: ignore[return-value]


@router.get("/admin/wallets/{user_id}", response_model=WalletSchema)
async def admin_get_wallet(
    user_id: int,
    current_user: AdminDep,
    wallet_repo: SQLAlchemyWalletRepository = Depends(_wallet_repo),
) -> WalletSchema:
    uc = AdminGetWalletUseCase(wallet_repo)
    try:
        wallet = await uc.execute(user_id)
    except WalletNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return WalletSchema.model_validate(wallet)
