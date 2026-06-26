"""Implémentation SQLAlchemy asynchrone du repository slider."""
from datetime import datetime, timezone

from sqlalchemy import asc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.slider.domain.entites import Slider
from app.modules.slider.domain.depots import AbstractSliderRepository
from app.modules.slider.infrastructure.modeles import SliderModel


def _to_entity(m: SliderModel) -> Slider:
    return Slider(
        id=m.id, titre=m.titre, sous_titre=m.sous_titre, image=m.image,
        lien=m.lien, texte_bouton=m.texte_bouton, position=m.position, est_actif=m.est_actif,
    )


class SQLSliderRepository(AbstractSliderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Slider]:
        requete = (
            select(SliderModel)
            .where(SliderModel.est_actif.is_(True), SliderModel.deleted_at.is_(None))
            .order_by(asc(SliderModel.position))
        )
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def get_by_id(self, slider_id: int) -> Slider | None:
        requete = select(SliderModel).where(
            SliderModel.id == slider_id, SliderModel.deleted_at.is_(None)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def create(
        self, titre: str, sous_titre: str | None, image: str, lien: str | None,
        texte_bouton: str | None, position: int, est_actif: bool
    ) -> Slider:
        modele = SliderModel(
            titre=titre, sous_titre=sous_titre, image=image, lien=lien,
            texte_bouton=texte_bouton, position=position, est_actif=est_actif,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

    async def update(
        self, slider_id: int, titre: str, sous_titre: str | None, image: str,
        lien: str | None, texte_bouton: str | None, position: int, est_actif: bool
    ) -> Slider | None:
        requete = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(
                titre=titre, sous_titre=sous_titre, image=image, lien=lien,
                texte_bouton=texte_bouton, position=position, est_actif=est_actif,
            )
            .returning(SliderModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def reorder(self, slider_id: int, position: int) -> Slider | None:
        requete = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(position=position)
            .returning(SliderModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def soft_delete(self, slider_id: int) -> bool:
        requete = (
            update(SliderModel)
            .where(SliderModel.id == slider_id, SliderModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        resultat = await self._session.execute(requete)
        return resultat.rowcount > 0
