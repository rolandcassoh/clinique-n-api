"""Implémentation SQLAlchemy asynchrone du repository paramètre (constant)."""
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.constante.domain.entites import Setting, SettingType
from app.modules.constante.domain.depots import AbstractSettingRepository
from app.modules.constante.infrastructure.modeles import SettingModel


def _to_entity(m: SettingModel) -> Setting:
    return Setting(
        id=m.id, cle=m.cle, raw_value=m.valeur,
        type=m.type,  # type: ignore[arg-type]
        groupe=m.groupe, est_public=m.est_public,
    )


class SQLSettingRepository(AbstractSettingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_public_frontend(self) -> list[Setting]:
        requete = select(SettingModel).where(
            SettingModel.est_public.is_(True),
            SettingModel.groupe == "frontend",
        )
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def get_public_by_key(self, cle: str) -> Setting | None:
        requete = select(SettingModel).where(
            SettingModel.cle == cle,
            SettingModel.est_public.is_(True),
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def list_all(self) -> list[Setting]:
        requete = select(SettingModel).order_by(SettingModel.cle)
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def update_value(self, cle: str, valeur: str | None) -> Setting | None:
        # MySQL ne supporte pas UPDATE ... RETURNING (syntaxe Postgres) : on met à jour
        # puis on relit la ligne.
        requete = update(SettingModel).where(SettingModel.cle == cle).values(valeur=valeur)
        resultat = await self._session.execute(requete)
        if resultat.rowcount == 0:
            return None
        modele = (
            await self._session.execute(select(SettingModel).where(SettingModel.cle == cle))
        ).scalar_one_or_none()
        return _to_entity(modele) if modele else None
