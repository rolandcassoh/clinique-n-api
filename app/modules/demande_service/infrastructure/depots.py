"""Implémentation SQLAlchemy async du repository RequestService."""
from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.demande_service.domain.entites import RequestService, RequestServiceStatus
from app.modules.demande_service.domain.depots import RequestServiceRepository
from app.modules.demande_service.infrastructure.modeles import RequestServiceModel
from app.shared.schemas.pagination import PaginationParams


def _to_entity(m: RequestServiceModel) -> RequestService:
    return RequestService(
        id=m.id,
        id_utilisateur=m.id_utilisateur,
        id_categorie=m.id_categorie,
        titre=m.titre,
        description=m.description,
        localisation=m.localisation,
        latitude=m.latitude,
        longitude=m.longitude,
        budget_min=m.budget_min,
        budget_max=m.budget_max,
        preferred_date=m.preferred_date,  # type: ignore[arg-type]
        creneau_prefere=m.creneau_prefere,  # type: ignore[arg-type]
        statut=RequestServiceStatus(m.statut),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyRequestServiceRepository(RequestServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user(
        self, id_utilisateur: int, params: PaginationParams
    ) -> tuple[list[RequestService], int]:
        """Liste les demandes de service d'un utilisateur avec pagination."""
        requete_base = select(RequestServiceModel).where(
            RequestServiceModel.id_utilisateur == id_utilisateur,
            RequestServiceModel.deleted_at.is_(None),
        )
        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()
        requete_lignes = requete_base.order_by(RequestServiceModel.id.desc()).offset(params.offset).limit(params.per_page)
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_to_entity(l) for l in lignes], total

    async def list_all(
        self, params: PaginationParams, statut: RequestServiceStatus | None = None
    ) -> tuple[list[RequestService], int]:
        """Liste toutes les demandes de service avec pagination et filtre optionnel par statut."""
        requete_base = select(RequestServiceModel).where(
            RequestServiceModel.deleted_at.is_(None),
        )
        if statut is not None:
            requete_base = requete_base.where(RequestServiceModel.statut == statut.valeur)
        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()
        requete_lignes = requete_base.order_by(RequestServiceModel.id.desc()).offset(params.offset).limit(params.per_page)
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_to_entity(l) for l in lignes], total

    async def get_by_id(self, request_id: int) -> RequestService | None:
        """Retourne une demande de service par son identifiant."""
        requete = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _to_entity(ligne) if ligne else None

    async def create(
        self,
        id_utilisateur: int,
        titre: str,
        description: str,
        id_categorie: int | None,
        localisation: str | None,
        latitude: Decimal | None,
        longitude: Decimal | None,
        budget_min: Decimal | None,
        budget_max: Decimal | None,
        preferred_date: date | None,
        creneau_prefere: time | None,
    ) -> RequestService:
        """Crée une nouvelle demande de service."""
        modele = RequestServiceModel(
            id_utilisateur=id_utilisateur,
            titre=titre,
            description=description,
            id_categorie=id_categorie,
            localisation=localisation,
            latitude=latitude,
            longitude=longitude,
            budget_min=budget_min,
            budget_max=budget_max,
            preferred_date=preferred_date,
            creneau_prefere=creneau_prefere,
            statut=RequestServiceStatus.PENDING.valeur,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _to_entity(modele)

    async def update_status(
        self, request_id: int, new_status: RequestServiceStatus
    ) -> RequestService | None:
        """Met à jour le statut d'une demande de service."""
        requete = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        ligne.statut = new_status.valeur
        await self._session.flush()
        await self._session.refresh(ligne)
        return _to_entity(ligne)

    async def soft_delete(self, request_id: int) -> bool:
        """Suppression logique d'une demande de service."""
        requete = select(RequestServiceModel).where(
            RequestServiceModel.id == request_id,
            RequestServiceModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
