from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.constant.api.schemas import SettingSchema, SettingUpdateSchema
from app.modules.constant.application.use_cases import ConstantUseCases
from app.modules.constant.domain.exceptions import SettingNotFoundError
from app.modules.constant.infrastructure.repositories import SQLSettingRepository

router = APIRouter(tags=["constants"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> ConstantUseCases:
    return ConstantUseCases(SQLSettingRepository(db))


@router.get("/constants", response_model=dict[str, Any])
async def get_public_constants(uc: ConstantUseCases = Depends(_use_cases)) -> dict[str, Any]:
    return await uc.get_public_frontend_constants()


@router.get("/constants/{key}", response_model=dict[str, Any])
async def get_public_constant(key: str, uc: ConstantUseCases = Depends(_use_cases)) -> dict[str, Any]:
    try:
        return await uc.get_public_constant(key)
    except SettingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/admin/settings", response_model=list[SettingSchema])
async def list_all_settings(
    uc: ConstantUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> list[SettingSchema]:
    settings = await uc.list_all_settings()
    return [SettingSchema.from_entity(s) for s in settings]


@router.put("/admin/settings/{key}", response_model=SettingSchema)
async def update_setting(
    key: str,
    body: SettingUpdateSchema,
    uc: ConstantUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SettingSchema:
    try:
        setting = await uc.update_setting(key, body.value)
    except SettingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return SettingSchema.from_entity(setting)
