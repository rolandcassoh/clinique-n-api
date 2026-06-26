"""Implémentation SQLAlchemy asynchrone du repository FAQ."""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.faq.domain.entites import FAQ
from app.modules.faq.domain.depots import FAQRepository
from app.modules.faq.infrastructure.modeles import FAQModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: FAQModel) -> FAQ:
    return FAQ(
        id=m.id,
        question=m.question,
        reponse=m.reponse,
        category=m.category,
        est_actif=m.est_actif,
        ordre_affichage=m.ordre_affichage,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyFAQRepository(FAQRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(
        self, params: PaginationParams, category: str | None = None
    ) -> tuple[list[FAQ], int]:
        requete_base = select(FAQModel).where(
            FAQModel.deleted_at.is_(None),
            FAQModel.est_actif.is_(True),
        )
        if category:
            requete_base = requete_base.where(FAQModel.category == category)

        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()

        requete_lignes = (
            requete_base.order_by(FAQModel.ordre_affichage, FAQModel.id)
            .offset(params.offset)
            .limit(params.per_page)
        )
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_to_entity(r) for r in lignes], total

    async def get_by_id(self, faq_id: int) -> FAQ | None:
        requete = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_entity(ligne) if ligne else None

    async def create(
        self,
        question: str,
        reponse: str,
        category: str | None,
        est_actif: bool,
        ordre_affichage: int,
    ) -> FAQ:
        faq = FAQModel(
            question=question,
            reponse=reponse,
            category=category,
            est_actif=est_actif,
            ordre_affichage=ordre_affichage,
        )
        self._session.add(faq)
        await self._session.flush()
        await self._session.refresh(faq)
        return _to_entity(faq)

    async def update(
        self,
        faq_id: int,
        question: str | None,
        reponse: str | None,
        category: str | None,
        est_actif: bool | None,
        ordre_affichage: int | None,
    ) -> FAQ | None:
        requete = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        if question is not None:
            ligne.question = question
        if reponse is not None:
            ligne.reponse = reponse
        if category is not None:
            ligne.category = category
        if est_actif is not None:
            ligne.est_actif = est_actif
        if ordre_affichage is not None:
            ligne.ordre_affichage = ordre_affichage
        await self._session.flush()
        await self._session.refresh(ligne)
        return _to_entity(ligne)

    async def soft_delete(self, faq_id: int) -> bool:
        requete = select(FAQModel).where(
            FAQModel.id == faq_id,
            FAQModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
