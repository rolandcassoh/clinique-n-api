"""Implémentation SQLAlchemy asynchrone du repository langue (language)."""
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.langue.domain.entites import Language
from app.modules.langue.domain.depots import AbstractLanguageRepository
from app.modules.langue.infrastructure.modeles import LanguageModel


def _to_entity(m: LanguageModel) -> Language:
    return Language(
        id=m.id, nom=m.nom, code=m.code, nom_natif=m.nom_natif,
        drapeau=m.drapeau, est_defaut=m.est_defaut, est_actif=m.est_actif,
        sens_ecriture=m.sens_ecriture,  # type: ignore[arg-type]
    )


class SQLLanguageRepository(AbstractLanguageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[Language]:
        requete = select(LanguageModel).where(
            LanguageModel.est_actif.is_(True),
            LanguageModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def get_default(self) -> Language | None:
        requete = select(LanguageModel).where(
            LanguageModel.est_defaut.is_(True),
            LanguageModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_id(self, language_id: int) -> Language | None:
        requete = select(LanguageModel).where(
            LanguageModel.id == language_id,
            LanguageModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_code(self, code: str) -> Language | None:
        requete = select(LanguageModel).where(
            LanguageModel.code == code,
            LanguageModel.deleted_at.is_(None),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def create(
        self, nom: str, code: str, nom_natif: str | None, drapeau: str | None,
        est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language:
        modele = LanguageModel(
            nom=nom, code=code, nom_natif=nom_natif, drapeau=drapeau,
            est_defaut=est_defaut, est_actif=est_actif, sens_ecriture=sens_ecriture,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

    async def update(
        self, language_id: int, nom: str, code: str, nom_natif: str | None,
        drapeau: str | None, est_defaut: bool, est_actif: bool, sens_ecriture: Literal["ltr", "rtl"]
    ) -> Language | None:
        requete = (
            update(LanguageModel)
            .where(LanguageModel.id == language_id, LanguageModel.deleted_at.is_(None))
            .values(
                nom=nom, code=code, nom_natif=nom_natif, drapeau=drapeau,
                est_defaut=est_defaut, est_actif=est_actif, sens_ecriture=sens_ecriture,
            )
            .returning(LanguageModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def set_default(self, language_id: int) -> Language | None:
        # Vérifier que la langue existe avant de modifier les autres
        cible = await self.get_by_id(language_id)
        if cible is None:
            return None

        # Remettre toutes les langues à est_defaut=False
        await self._session.execute(
            update(LanguageModel)
            .where(LanguageModel.deleted_at.is_(None))
            .values(est_defaut=False)
        )
        requete = (
            update(LanguageModel)
            .where(LanguageModel.id == language_id)
            .values(est_defaut=True)
            .returning(LanguageModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None
