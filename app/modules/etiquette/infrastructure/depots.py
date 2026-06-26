"""Implémentation SQLAlchemy asynchrone du repository tag."""
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.etiquette.domain.entites import Tag
from app.modules.etiquette.domain.depots import AbstractTagRepository
from app.modules.etiquette.infrastructure.modeles import TagModel


def _to_entity(m: TagModel) -> Tag:
    return Tag(id=m.id, nom=m.nom, identifiant_url=m.identifiant_url, type=m.type, created_at=m.created_at)


class SQLTagRepository(AbstractTagRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, type_filter: str | None = None, search: str | None = None) -> list[Tag]:
        requete = select(TagModel).where(TagModel.deleted_at.is_(None))
        if type_filter:
            requete = requete.where(TagModel.type == type_filter)
        if search:
            requete = requete.where(TagModel.nom.ilike(f"%{search}%"))
        requete = requete.limit(100)
        resultat = await self._session.execute(requete)
        return [_to_entity(ligne) for ligne in resultat.scalars().all()]

    async def get_by_id(self, tag_id: int) -> Tag | None:
        requete = select(TagModel).where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def get_by_slug(self, identifiant_url: str) -> Tag | None:
        requete = select(TagModel).where(TagModel.identifiant_url == identifiant_url, TagModel.deleted_at.is_(None))
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def create(self, nom: str, identifiant_url: str, type: str | None) -> Tag:
        modele = TagModel(nom=nom, identifiant_url=identifiant_url, type=type)
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

    async def update(self, tag_id: int, nom: str, identifiant_url: str, type: str | None) -> Tag | None:
        requete = (
            update(TagModel)
            .where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
            .values(nom=nom, identifiant_url=identifiant_url, type=type)
            .returning(TagModel)
        )
        resultat = await self._session.execute(requete)
        modele = resultat.scalar_one_or_none()
        return _to_entity(modele) if modele else None

    async def soft_delete(self, tag_id: int) -> bool:
        requete = (
            update(TagModel)
            .where(TagModel.id == tag_id, TagModel.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        resultat = await self._session.execute(requete)
        return resultat.rowcount > 0
