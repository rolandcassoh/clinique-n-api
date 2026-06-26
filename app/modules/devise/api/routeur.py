"""Routeur FastAPI du module devise (devise)."""
from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.devise.api.schemas import CurrencyCreateSchema, CurrencySchema, CurrencyUpdateSchema
from app.modules.devise.application.cas_utilisation import CurrencyUseCases
from app.modules.devise.domain.exceptions import CurrencyCodeConflictError, CurrencyNotFoundError
from app.modules.devise.infrastructure.depots import SQLCurrencyRepository

router = APIRouter(tags=["devises"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> CurrencyUseCases:
    return CurrencyUseCases(SQLCurrencyRepository(db))


def _to_schema(c) -> CurrencySchema:
    return CurrencySchema.model_validate(c.__dict__)


@router.get("/devises", response_model=list[CurrencySchema])
async def list_currencies(uc: CurrencyUseCases = Depends(_use_cases)) -> list[CurrencySchema]:
    """Liste toutes les devises actives."""
    devises = await uc.list_active()
    return [_to_schema(c) for c in devises]


@router.get("/devises/defaut", response_model=CurrencySchema)
async def get_default_currency(uc: CurrencyUseCases = Depends(_use_cases)) -> CurrencySchema:
    """Retourne la devise par défaut."""
    try:
        devise = await uc.get_default()
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(devise)


@router.get("/devises/{code}", response_model=CurrencySchema)
async def get_currency_by_code(code: str, uc: CurrencyUseCases = Depends(_use_cases)) -> CurrencySchema:
    """Retourne une devise par son code ISO."""
    try:
        devise = await uc.get_by_code(code)
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(devise)


@router.post("/admin/devises", response_model=CurrencySchema, status_code=statut.HTTP_201_CREATED)
async def create_currency(
    body: CurrencyCreateSchema,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    """Créer une devise (admin)."""
    try:
        devise = await uc.create_currency(
            nom=body.nom, code=body.code, symbole=body.symbole,
            taux_change=body.taux_change, est_defaut=body.est_defaut, est_actif=body.est_actif,
        )
    except CurrencyCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(devise)


@router.put("/admin/devises/{currency_id}", response_model=CurrencySchema)
async def update_currency(
    currency_id: int,
    body: CurrencyUpdateSchema,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    """Modifier une devise (admin)."""
    try:
        devise = await uc.update_currency(
            currency_id, nom=body.nom, code=body.code, symbole=body.symbole,
            taux_change=body.taux_change, est_defaut=body.est_defaut, est_actif=body.est_actif,
        )
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    except CurrencyCodeConflictError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc))
    return _to_schema(devise)


@router.patch("/admin/devises/{currency_id}/definir-defaut", response_model=CurrencySchema)
async def set_default_currency(
    currency_id: int,
    uc: CurrencyUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> CurrencySchema:
    """Définir la devise par défaut (admin)."""
    try:
        devise = await uc.set_default(currency_id)
    except CurrencyNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(devise)
