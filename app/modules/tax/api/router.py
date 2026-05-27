from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.tax.api.schemas import TaxCreateSchema, TaxSchema, TaxUpdateSchema
from app.modules.tax.application.use_cases import (
    CreateTaxUseCase,
    DeleteTaxUseCase,
    GetDefaultTaxUseCase,
    GetTaxUseCase,
    ListActiveTaxesUseCase,
    SetDefaultTaxUseCase,
    UpdateTaxUseCase,
)
from app.modules.tax.domain.exceptions import NoDefaultTaxError, TaxNotFoundError
from app.modules.tax.infrastructure.repositories import SQLTaxRepository

router = APIRouter(tags=["taxes"])


def _repo(db: AsyncSession = Depends(get_db)) -> SQLTaxRepository:
    return SQLTaxRepository(db)


# ── Public ──────────────────────────────────────────────────────────────────


@router.get("/taxes", response_model=list[TaxSchema])
async def list_taxes(
    repo: SQLTaxRepository = Depends(_repo),
) -> list[TaxSchema]:
    taxes = await ListActiveTaxesUseCase(repo).execute()
    return [TaxSchema.model_validate(t.__dict__) for t in taxes]


@router.get("/taxes/default", response_model=TaxSchema)
async def get_default_tax(
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await GetDefaultTaxUseCase(repo).execute()
    except NoDefaultTaxError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.get("/taxes/{tax_id}", response_model=TaxSchema)
async def get_tax(
    tax_id: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await GetTaxUseCase(repo).execute(tax_id)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


# ── Admin ────────────────────────────────────────────────────────────────────


@router.post(
    "/admin/taxes",
    response_model=TaxSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_tax(
    body: TaxCreateSchema,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    tax = await CreateTaxUseCase(repo).execute(
        name=body.name,
        rate=body.rate,
        type=body.type,
        country_id=body.country_id,
        is_default=body.is_default,
        is_active=body.is_active,
    )
    return TaxSchema.model_validate(tax.__dict__)


@router.put(
    "/admin/taxes/{tax_id}",
    response_model=TaxSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_tax(
    tax_id: int,
    body: TaxUpdateSchema,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await UpdateTaxUseCase(repo).execute(
            tax_id=tax_id,
            name=body.name,
            rate=body.rate,
            type=body.type,
            country_id=body.country_id,
            is_default=body.is_default,
            is_active=body.is_active,
        )
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.patch(
    "/admin/taxes/{tax_id}/set-default",
    response_model=TaxSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def set_default_tax(
    tax_id: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await SetDefaultTaxUseCase(repo).execute(tax_id)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.delete(
    "/admin/taxes/{tax_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_tax(
    tax_id: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> None:
    try:
        await DeleteTaxUseCase(repo).execute(tax_id)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)
