"""Routeur FastAPI du module slider — gestion des bannières défilantes."""
from fastapi import APIRouter, Depends, HTTPException, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.slider.api.schemas import (
    SliderCreateSchema,
    SliderReorderSchema,
    SliderSchema,
    SliderUpdateSchema,
)
from app.modules.slider.application.cas_utilisation import SliderUseCases
from app.modules.slider.domain.exceptions import SliderNotFoundError
from app.modules.slider.infrastructure.depots import SQLSliderRepository

router = APIRouter(tags=["Sliders"])


def _use_cases(db: AsyncSession = Depends(get_db)) -> SliderUseCases:
    return SliderUseCases(SQLSliderRepository(db))


def _to_schema(s) -> SliderSchema:
    return SliderSchema.model_validate(s.__dict__)


@router.get("/sliders", response_model=list[SliderSchema])
async def list_sliders(uc: SliderUseCases = Depends(_use_cases)) -> list[SliderSchema]:
    """Liste les bannières actives triées par position."""
    bannieres = await uc.list_active()
    return [_to_schema(s) for s in bannieres]


@router.post("/admin/sliders", response_model=SliderSchema, status_code=statut.HTTP_201_CREATED)
async def create_slider(
    body: SliderCreateSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    """Créer une bannière (admin)."""
    banniere = await uc.create_slider(
        titre=body.titre, sous_titre=body.sous_titre, image=body.image,
        lien=body.lien, texte_bouton=body.texte_bouton,
        position=body.position, est_actif=body.est_actif,
    )
    return _to_schema(banniere)


@router.put("/admin/sliders/{slider_id}", response_model=SliderSchema)
async def update_slider(
    slider_id: int,
    body: SliderUpdateSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    """Modifier une bannière (admin)."""
    try:
        banniere = await uc.update_slider(
            slider_id, titre=body.titre, sous_titre=body.sous_titre, image=body.image,
            lien=body.lien, texte_bouton=body.texte_bouton,
            position=body.position, est_actif=body.est_actif,
        )
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(banniere)


@router.delete("/admin/sliders/{slider_id}", status_code=statut.HTTP_204_NO_CONTENT)
async def delete_slider(
    slider_id: int,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> None:
    try:
        await uc.delete_slider(slider_id)
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch("/admin/sliders/{slider_id}/reordonner", response_model=SliderSchema)
async def reorder_slider(
    slider_id: int,
    body: SliderReorderSchema,
    uc: SliderUseCases = Depends(_use_cases),
    _: dict = Depends(require_role("admin", "super-admin")),
) -> SliderSchema:
    """Réordonner une bannière (admin)."""
    try:
        banniere = await uc.reorder_slider(slider_id, body.position)
    except SliderNotFoundError as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc))
    return _to_schema(banniere)
