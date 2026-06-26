"""Routeur FastAPI du module constant — paramètres système publics et admin."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.constante.api.schemas import SettingSchema, SettingUpdateSchema
from app.modules.constante.application.cas_utilisation import ConstantUseCases
from app.modules.constante.domain.exceptions import SettingNotFoundError
from app.modules.constante.infrastructure.depots import SQLSettingRepository

router = APIRouter(tags=["constantes"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> ConstantUseCases:
    return ConstantUseCases(SQLSettingRepository(db))


@router.get("/constantes", response_model=dict[str, Any])
async def get_public_constants(uc: ConstantUseCases = Depends(_use_cases)) -> dict[str, Any]:
    """Retourne tous les paramètres publics frontend sous forme clé→valeur."""
    return await uc.get_public_frontend_constants()


@router.get("/constantes/{cle}", response_model=dict[str, Any])
async def get_public_constant(cle: str, uc: ConstantUseCases = Depends(_use_cases)) -> dict[str, Any]:
    """Retourne un paramètre public par sa clé."""
    try:
        return await uc.get_public_constant(cle)
    except SettingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/admin/parametres", response_model=list[SettingSchema])
async def list_all_settings(
    uc: ConstantUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> list[SettingSchema]:
    """Liste tous les paramètres système (admin)."""
    parametres = await uc.list_all_settings()
    return [SettingSchema.from_entity(s) for s in parametres]


@router.put("/admin/parametres/{cle}", response_model=SettingSchema)
async def update_setting(
    cle: str,
    body: SettingUpdateSchema,
    uc: ConstantUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SettingSchema:
    """Modifier la valeur d'un paramètre (admin)."""
    try:
        parametre = await uc.update_setting(cle, body.valeur)
    except SettingNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return SettingSchema.from_entity(parametre)
