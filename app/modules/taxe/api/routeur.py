from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.taxe.api.schemas import TaxCreateSchema, TaxSchema, TaxUpdateSchema
from app.modules.taxe.application.cas_utilisation import (
    CreateTaxUseCase,
    DeleteTaxUseCase,
    GetDefaultTaxUseCase,
    GetTaxUseCase,
    ListActiveTaxesUseCase,
    SetDefaultTaxUseCase,
    UpdateTaxUseCase,
)
from app.modules.taxe.domain.exceptions import NoDefaultTaxError, TaxNotFoundError
from app.modules.taxe.infrastructure.depots import SQLTaxRepository

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
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.get("/taxes/{id_taxe}", response_model=TaxSchema)
async def get_tax(
    id_taxe: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await GetTaxUseCase(repo).execute(id_taxe)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


# ── Admin ────────────────────────────────────────────────────────────────────


@router.post(
    "/admin/taxes",
    response_model=TaxSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_tax(
    body: TaxCreateSchema,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    tax = await CreateTaxUseCase(repo).execute(
        nom=body.nom,
        tarif=body.tarif,
        type=body.type,
        id_pays=body.id_pays,
        est_defaut=body.est_defaut,
        est_actif=body.est_actif,
    )
    return TaxSchema.model_validate(tax.__dict__)


@router.put(
    "/admin/taxes/{id_taxe}",
    response_model=TaxSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_tax(
    id_taxe: int,
    body: TaxUpdateSchema,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await UpdateTaxUseCase(repo).execute(
            id_taxe=id_taxe,
            nom=body.nom,
            tarif=body.tarif,
            type=body.type,
            id_pays=body.id_pays,
            est_defaut=body.est_defaut,
            est_actif=body.est_actif,
        )
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.patch(
    "/admin/taxes/{id_taxe}/definir-defaut",
    response_model=TaxSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def set_default_tax(
    id_taxe: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> TaxSchema:
    try:
        tax = await SetDefaultTaxUseCase(repo).execute(id_taxe)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
    return TaxSchema.model_validate(tax.__dict__)


@router.delete(
    "/admin/taxes/{id_taxe}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_tax(
    id_taxe: int,
    repo: SQLTaxRepository = Depends(_repo),
) -> None:
    try:
        await DeleteTaxUseCase(repo).execute(id_taxe)
    except TaxNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=exc.message)
