from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.currency.api.schemas import CurrencyCreateSchema, CurrencySchema, CurrencyUpdateSchema
from app.modules.currency.application.use_cases import CurrencyUseCases
from app.modules.currency.domain.exceptions import CurrencyCodeConflictError, CurrencyNotFoundError
from app.modules.currency.infrastructure.repositories import SQLCurrencyRepository

router = APIRouter(tags=["currencies"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> CurrencyUseCases:
    return CurrencyUseCases(SQLCurrencyRepository(db))


def _to_schema(c) -> CurrencySchema:
    return CurrencySchema.model_validate(c.__dict__)


@router.get("/currencies", response_model=list[CurrencySchema])
async def list_currencies(uc: CurrencyUseCases = Depends(_use_cases)) -> list[CurrencySchema]:
    currencies = await uc.list_active()
    return [_to_schema(c) for c in currencies]


@router.get("/currencies/default", response_model=CurrencySchema)
async def get_default_currency(uc: CurrencyUseCases = Depends(_use_cases)) -> CurrencySchema:
    try:
        currency = await uc.get_default()
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(currency)


@router.get("/currencies/{code}", response_model=CurrencySchema)
async def get_currency_by_code(code: str, uc: CurrencyUseCases = Depends(_use_cases)) -> CurrencySchema:
    try:
        currency = await uc.get_by_code(code)
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(currency)


@router.post("/admin/currencies", response_model=CurrencySchema, status_code=status.HTTP_201_CREATED)
async def create_currency(
    body: CurrencyCreateSchema,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    try:
        currency = await uc.create_currency(
            name=body.name, code=body.code, symbol=body.symbol,
            exchange_rate=body.exchange_rate, is_default=body.is_default, is_active=body.is_active,
        )
    except CurrencyCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(currency)


@router.put("/admin/currencies/{currency_id}", response_model=CurrencySchema)
async def update_currency(
    currency_id: int,
    body: CurrencyUpdateSchema,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    try:
        currency = await uc.update_currency(
            currency_id, name=body.name, code=body.code, symbol=body.symbol,
            exchange_rate=body.exchange_rate, is_default=body.is_default, is_active=body.is_active,
        )
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except CurrencyCodeConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(currency)


@router.patch("/admin/currencies/{currency_id}/set-default", response_model=CurrencySchema)
async def set_default_currency(
    currency_id: int,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    try:
        currency = await uc.set_default(currency_id)
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(currency)
