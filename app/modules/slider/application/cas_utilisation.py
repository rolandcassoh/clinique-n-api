"""Cas d'utilisation du module slider."""
from app.modules.slider.domain.entites import Slider
from app.modules.slider.domain.exceptions import SliderNotFoundError
from app.modules.slider.domain.depots import AbstractSliderRepository


class SliderUseCases:
    def __init__(self, repo: AbstractSliderRepository) -> None:
        self._repo = repo

    async def list_active(self) -> list[Slider]:
        return await self._repo.list_active()

    async def create_slider(
        self, titre: str, sous_titre: str | None, image: str, lien: str | None,
        texte_bouton: str | None, position: int = 0, est_actif: bool = True
    ) -> Slider:
        return await self._repo.create(
            titre=titre, sous_titre=sous_titre, image=image, lien=lien,
            texte_bouton=texte_bouton, position=position, est_actif=est_actif,
        )

    async def update_slider(
        self, slider_id: int, titre: str, sous_titre: str | None, image: str,
        lien: str | None, texte_bouton: str | None, position: int, est_actif: bool
    ) -> Slider:
        mis_a_jour = await self._repo.update(
            slider_id, titre=titre, sous_titre=sous_titre, image=image, lien=lien,
            texte_bouton=texte_bouton, position=position, est_actif=est_actif,
        )
        if mis_a_jour is None:
            raise SliderNotFoundError(slider_id)
        return mis_a_jour

    async def reorder_slider(self, slider_id: int, position: int) -> Slider:
        banniere = await self._repo.reorder(slider_id, position)
        if banniere is None:
            raise SliderNotFoundError(slider_id)
        return banniere

    async def delete_slider(self, slider_id: int) -> None:
        supprime = await self._repo.soft_delete(slider_id)
        if not supprime:
            raise SliderNotFoundError(slider_id)
