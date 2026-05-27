from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.slider.api.schemas import (
    SliderCreateSchema,
    SliderReorderSchema,
    SliderSchema,
    SliderUpdateSchema,
)
from app.modules.slider.application.use_cases import SliderUseCases
from app.modules.slider.domain.exceptions import SliderNotFoundError
from app.modules.slider.infrastructure.repositories import SQLSliderRepository

router = APIRouter(tags=["sliders"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> SliderUseCases:
    return SliderUseCases(SQLSliderRepository(db))


def _to_schema(s) -> SliderSchema:
    return SliderSchema.model_validate(s.__dict__)


@router.get("/sliders", response_model=list[SliderSchema])
async def list_sliders(uc: SliderUseCases = Depends(_use_cases)) -> list[SliderSchema]:
    sliders = await uc.list_active()
    return [_to_schema(s) for s in sliders]


@router.post("/admin/sliders", response_model=SliderSchema, status_code=status.HTTP_201_CREATED)
async def create_slider(
    body: SliderCreateSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    slider = await uc.create_slider(
        title=body.title, subtitle=body.subtitle, image=body.image,
        link=body.link, button_text=body.button_text,
        position=body.position, is_active=body.is_active,
    )
    return _to_schema(slider)


@router.put("/admin/sliders/{slider_id}", response_model=SliderSchema)
async def update_slider(
    slider_id: int,
    body: SliderUpdateSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    try:
        slider = await uc.update_slider(
            slider_id, title=body.title, subtitle=body.subtitle, image=body.image,
            link=body.link, button_text=body.button_text,
            position=body.position, is_active=body.is_active,
        )
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(slider)


@router.delete("/admin/sliders/{slider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slider(
    slider_id: int,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> None:
    try:
        await uc.delete_slider(slider_id)
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/admin/sliders/{slider_id}/reorder", response_model=SliderSchema)
async def reorder_slider(
    slider_id: int,
    body: SliderReorderSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    try:
        slider = await uc.reorder_slider(slider_id, body.position)
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(slider)
