"""Implémentation SQLAlchemy async des repositories Logistic."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.logistique.domain.entites import ShippingRate, ShippingZone
from app.modules.logistique.domain.depots import ShippingRateRepository, ShippingZoneRepository
from app.modules.logistique.infrastructure.modeles import ShippingRateModel, ShippingZoneModel


def _zone_to_entity(m: ShippingZoneModel) -> ShippingZone:
    return ShippingZone(
        id=m.id, nom=m.nom, description=m.description, est_actif=m.est_actif,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _rate_to_entity(m: ShippingRateModel) -> ShippingRate:
    return ShippingRate(
        id=m.id, id_zone=m.id_zone, nom=m.nom,
        poids_min=m.poids_min, poids_max=m.poids_max,
        montant_min_commande=m.montant_min_commande, tarif=m.tarif,
        livraison_gratuite=m.livraison_gratuite,
        jours_livraison_min=m.jours_livraison_min, jours_livraison_max=m.jours_livraison_max,
        est_actif=m.est_actif, created_at=m.created_at, updated_at=m.updated_at,
    )


class SQLAlchemyShippingZoneRepository(ShippingZoneRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> list[ShippingZone]:
        """Retourne toutes les zones de livraison actives."""
        requete = select(ShippingZoneModel).where(
            ShippingZoneModel.deleted_at.is_(None),
            ShippingZoneModel.est_actif.is_(True),
        ).order_by(ShippingZoneModel.id)
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_zone_to_entity(l) for l in lignes]

    async def get_by_id(self, id_zone: int) -> ShippingZone | None:
        """Retourne une zone de livraison par son identifiant."""
        requete = select(ShippingZoneModel).where(
            ShippingZoneModel.id == id_zone,
            ShippingZoneModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _zone_to_entity(ligne) if ligne else None

    async def create(self, nom: str, description: str | None, est_actif: bool) -> ShippingZone:
        """Crée une nouvelle zone de livraison."""
        modele = ShippingZoneModel(nom=nom, description=description, est_actif=est_actif)
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _zone_to_entity(modele)

    async def update(
        self, id_zone: int, nom: str | None, description: str | None, est_actif: bool | None
    ) -> ShippingZone | None:
        """Met à jour une zone de livraison existante."""
        requete = select(ShippingZoneModel).where(
            ShippingZoneModel.id == id_zone,
            ShippingZoneModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        if nom is not None:
            ligne.nom = nom
        if description is not None:
            ligne.description = description
        if est_actif is not None:
            ligne.est_actif = est_actif
        await self._session.flush()
        await self._session.refresh(ligne)
        return _zone_to_entity(ligne)

    async def soft_delete(self, id_zone: int) -> bool:
        """Suppression logique d'une zone de livraison."""
        requete = select(ShippingZoneModel).where(
            ShippingZoneModel.id == id_zone,
            ShippingZoneModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


class SQLAlchemyShippingRateRepository(ShippingRateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_zone(
        self, id_zone: int, min_amount: Decimal | None = None
    ) -> list[ShippingRate]:
        """Liste les tarifs actifs d'une zone, filtrés par montant minimum si fourni."""
        requete = select(ShippingRateModel).where(
            ShippingRateModel.id_zone == id_zone,
            ShippingRateModel.deleted_at.is_(None),
            ShippingRateModel.est_actif.is_(True),
        )
        if min_amount is not None:
            requete = requete.where(ShippingRateModel.montant_min_commande <= min_amount)
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_rate_to_entity(l) for l in lignes]

    async def get_by_id(self, rate_id: int) -> ShippingRate | None:
        """Retourne un tarif de livraison par son identifiant."""
        requete = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _rate_to_entity(ligne) if ligne else None

    async def create(
        self, id_zone: int, nom: str, poids_min: Decimal, poids_max: Decimal | None,
        montant_min_commande: Decimal, tarif: Decimal, livraison_gratuite: bool,
        jours_livraison_min: int, jours_livraison_max: int, est_actif: bool,
    ) -> ShippingRate:
        """Crée un nouveau tarif de livraison."""
        modele = ShippingRateModel(
            id_zone=id_zone, nom=nom, poids_min=poids_min, poids_max=poids_max,
            montant_min_commande=montant_min_commande, tarif=tarif, livraison_gratuite=livraison_gratuite,
            jours_livraison_min=jours_livraison_min, jours_livraison_max=jours_livraison_max,
            est_actif=est_actif,
        )
        self._session.add(modele)
        await self._session.flush()
        await self._session.refresh(modele)
        return _rate_to_entity(modele)

    async def update(
        self, rate_id: int, nom: str | None, poids_min: Decimal | None,
        poids_max: Decimal | None, montant_min_commande: Decimal | None, tarif: Decimal | None,
        livraison_gratuite: bool | None, jours_livraison_min: int | None,
        jours_livraison_max: int | None, est_actif: bool | None,
    ) -> ShippingRate | None:
        """Met à jour un tarif de livraison existant."""
        requete = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        for attribut, valeur in [
            ("nom", nom), ("poids_min", poids_min), ("poids_max", poids_max),
            ("montant_min_commande", montant_min_commande), ("tarif", tarif),
            ("livraison_gratuite", livraison_gratuite), ("jours_livraison_min", jours_livraison_min),
            ("jours_livraison_max", jours_livraison_max), ("est_actif", est_actif),
        ]:
            if valeur is not None:
                setattr(ligne, attribut, valeur)
        await self._session.flush()
        await self._session.refresh(ligne)
        return _rate_to_entity(ligne)

    async def soft_delete(self, rate_id: int) -> bool:
        """Suppression logique d'un tarif de livraison."""
        requete = select(ShippingRateModel).where(
            ShippingRateModel.id == rate_id,
            ShippingRateModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
