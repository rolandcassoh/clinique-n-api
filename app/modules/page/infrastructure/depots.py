"""Implémentation SQLAlchemy asynchrone du repository page (CMS)."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.page.domain.entites import Page
from app.modules.page.domain.depots import PageRepository
from app.modules.page.infrastructure.modeles import PageModel


def _to_entity(m: PageModel) -> Page:
    return Page(
        id=m.id,
        titre=m.titre,
        identifiant_url=m.identifiant_url,
        contenu=m.contenu,
        titre_meta=m.titre_meta,
        meta_description=m.meta_description,
        est_publie=m.est_publie,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyPageRepository(PageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_published(self) -> list[Page]:
        requete = (
            select(PageModel)
            .where(
                PageModel.deleted_at.is_(None),
                PageModel.est_publie.is_(True),
            )
            .order_by(PageModel.titre)
        )
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_to_entity(r) for r in lignes]

    async def get_by_slug(self, identifiant_url: str) -> Page | None:
        requete = select(PageModel).where(
            PageModel.identifiant_url == identifiant_url,
            PageModel.deleted_at.is_(None),
            PageModel.est_publie.is_(True),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_entity(ligne) if ligne else None

    async def get_by_id(self, page_id: int) -> Page | None:
        requete = select(PageModel).where(
            PageModel.id == page_id,
            PageModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_entity(ligne) if ligne else None

    async def create(
        self,
        titre: str,
        identifiant_url: str,
        contenu: str,
        titre_meta: str | None,
        meta_description: str | None,
        est_publie: bool,
    ) -> Page:
        page = PageModel(
            titre=titre,
            identifiant_url=identifiant_url,
            contenu=contenu,
            titre_meta=titre_meta,
            meta_description=meta_description,
            est_publie=est_publie,
        )
        self._session.add(page)
        await self._session.flush()
        await self._session.refresh(page)
        return _to_entity(page)

    async def update(
        self,
        page_id: int,
        titre: str | None,
        identifiant_url: str | None,
        contenu: str | None,
        titre_meta: str | None,
        meta_description: str | None,
        est_publie: bool | None,
    ) -> Page | None:
        requete = select(PageModel).where(
            PageModel.id == page_id,
            PageModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None

        if titre is not None:
            ligne.titre = titre
        if identifiant_url is not None:
            ligne.identifiant_url = identifiant_url
        if contenu is not None:
            ligne.contenu = contenu
        if titre_meta is not None:
            ligne.titre_meta = titre_meta
        if meta_description is not None:
            ligne.meta_description = meta_description
        if est_publie is not None:
            ligne.est_publie = est_publie

        await self._session.flush()
        await self._session.refresh(ligne)
        return _to_entity(ligne)
