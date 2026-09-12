"""Implémentation SQLAlchemy async des repositories Service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.service.domain.entites import (
    Service,
    ServiceCategory,
    ServiceEmployee,
    ServiceGallery,
    ServicePackage,
    ServiceReview,
)
from app.modules.service.domain.depots import (
    ServiceCategoryRepository,
    ServiceEmployeeRepository,
    ServiceGalleryRepository,
    ServicePackageRepository,
    ServiceRepository,
    ServiceReviewRepository,
)
from app.modules.service.infrastructure.modeles import (
    ServiceCategoryModel,
    ServiceEmployeeModel,
    ServiceGalleryModel,
    ServiceModel,
    ServicePackageModel,
    ServiceReviewModel,
)
from app.shared.schemas.pagination import PaginationParams


# ---------------------------------------------------------------------------
# Mappers
# ---------------------------------------------------------------------------

def _cat_to_entity(m: ServiceCategoryModel) -> ServiceCategory:
    return ServiceCategory(
        id=m.id, nom=m.nom, identifiant_url=m.identifiant_url, image=m.image,
        description=m.description, est_actif=m.est_actif, ordre_affichage=m.ordre_affichage,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _pkg_to_entity(m: ServicePackageModel) -> ServicePackage:
    return ServicePackage(
        id=m.id, id_service=m.id_service, nom=m.nom, description=m.description,
        prix=m.prix, nombre_seances=m.nombre_seances, jours_validite=m.jours_validite,
        est_actif=m.est_actif, created_at=m.created_at, updated_at=m.updated_at,
    )


def _emp_to_entity(m: ServiceEmployeeModel) -> ServiceEmployee:
    return ServiceEmployee(
        id=m.id, id_service=m.id_service, id_utilisateur=m.id_utilisateur, est_principal=m.est_principal,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _gallery_to_entity(m: ServiceGalleryModel) -> ServiceGallery:
    return ServiceGallery(
        id=m.id, id_service=m.id_service, image=m.image, legende=m.legende,
        ordre_affichage=m.ordre_affichage, created_at=m.created_at, updated_at=m.updated_at,
    )


def _review_to_entity(m: ServiceReviewModel) -> ServiceReview:
    return ServiceReview(
        id=m.id, id_service=m.id_service, id_utilisateur=m.id_utilisateur, note=m.note,
        commentaire=m.commentaire, est_approuve=m.est_approuve,
        created_at=m.created_at, updated_at=m.updated_at,
    )


def _svc_to_entity(
    m: ServiceModel,
    avg_rating: float | None = None,
    review_count: int = 0,
) -> Service:
    cat = _cat_to_entity(m.category) if m.category else None
    galleries = [_gallery_to_entity(g) for g in (m.galleries or [])]
    packages = [_pkg_to_entity(p) for p in (m.packages or [])]
    employees = [_emp_to_entity(e) for e in (m.employees or [])]
    return Service(
        id=m.id, id_prestataire=m.id_prestataire, id_categorie=m.id_categorie,
        nom=m.nom, identifiant_url=m.identifiant_url, description=m.description,
        short_description=m.short_description, prix=m.prix,
        prix_remise=m.prix_remise, duree_minutes=m.duree_minutes,
        est_actif=m.est_actif, est_mis_en_avant=m.est_mis_en_avant,
        service_domicile=m.service_domicile, max_membres=m.max_membres,
        created_at=m.created_at, updated_at=m.updated_at,
        category=cat, galleries=galleries, packages=packages, employees=employees,
        note_moyenne=avg_rating, review_count=review_count,
    )


# ---------------------------------------------------------------------------
# ServiceCategory
# ---------------------------------------------------------------------------

class SQLAlchemyServiceCategoryRepository(ServiceCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self, params: PaginationParams) -> tuple[list[ServiceCategory], int]:
        requete_base = select(ServiceCategoryModel).where(
            ServiceCategoryModel.deleted_at.is_(None),
            ServiceCategoryModel.est_actif.is_(True),
        )
        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()
        requete_lignes = requete_base.order_by(ServiceCategoryModel.ordre_affichage, ServiceCategoryModel.id).offset(params.offset).limit(params.per_page)
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_cat_to_entity(r) for r in lignes], total

    async def get_by_slug(self, identifiant_url: str) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.identifiant_url == identifiant_url,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(ligne) if ligne else None

    async def get_by_id(self, id_categorie: int) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == id_categorie,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _cat_to_entity(ligne) if ligne else None

    async def create(
        self, nom: str, identifiant_url: str, image: str | None, description: str | None,
        est_actif: bool, ordre_affichage: int,
    ) -> ServiceCategory:
        m = ServiceCategoryModel(
            nom=nom, identifiant_url=identifiant_url, image=image, description=description,
            est_actif=est_actif, ordre_affichage=ordre_affichage,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _cat_to_entity(m)

    async def update(
        self, id_categorie: int, nom: str | None, identifiant_url: str | None, image: str | None,
        description: str | None, est_actif: bool | None, ordre_affichage: int | None,
    ) -> ServiceCategory | None:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == id_categorie,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        if nom is not None:
            ligne.nom = nom
        if identifiant_url is not None:
            ligne.identifiant_url = identifiant_url
        if image is not None:
            ligne.image = image
        if description is not None:
            ligne.description = description
        if est_actif is not None:
            ligne.est_actif = est_actif
        if ordre_affichage is not None:
            ligne.ordre_affichage = ordre_affichage
        await self._session.flush()
        await self._session.refresh(ligne)
        return _cat_to_entity(ligne)

    async def soft_delete(self, id_categorie: int) -> bool:
        q = select(ServiceCategoryModel).where(
            ServiceCategoryModel.id == id_categorie,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def slug_exists(self, identifiant_url: str, exclude_id: int | None = None) -> bool:
        q = select(func.count()).select_from(ServiceCategoryModel).where(
            ServiceCategoryModel.identifiant_url == identifiant_url,
            ServiceCategoryModel.deleted_at.is_(None),
        )
        if exclude_id is not None:
            q = q.where(ServiceCategoryModel.id != exclude_id)
        return (await self._session.execute(q)).scalar_one() > 0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class SQLAlchemyServiceRepository(ServiceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self):
        return (
            select(ServiceModel)
            .where(ServiceModel.deleted_at.is_(None), ServiceModel.est_actif.is_(True))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )

    async def list_public(
        self,
        params: PaginationParams,
        id_categorie: int | None = None,
        search: str | None = None,
        service_domicile: bool | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
    ) -> tuple[list[Service], int]:
        requete_base = select(ServiceModel).where(
            ServiceModel.deleted_at.is_(None),
            ServiceModel.est_actif.is_(True),
        )
        if id_categorie is not None:
            requete_base = requete_base.where(ServiceModel.id_categorie == id_categorie)
        if search is not None:
            requete_base = requete_base.where(ServiceModel.nom.ilike(f"%{search}%"))
        if service_domicile is not None:
            requete_base = requete_base.where(ServiceModel.service_domicile == service_domicile)
        if min_price is not None:
            requete_base = requete_base.where(ServiceModel.prix >= min_price)
        if max_price is not None:
            requete_base = requete_base.where(ServiceModel.prix <= max_price)

        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()

        requete_lignes = (
            requete_base.options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
            .order_by(ServiceModel.id)
            .offset(params.offset)
            .limit(params.per_page)
        )
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_svc_to_entity(r) for r in lignes], total

    async def get_by_slug(self, identifiant_url: str) -> Service | None:
        q = (
            select(ServiceModel)
            .where(ServiceModel.identifiant_url == identifiant_url, ServiceModel.deleted_at.is_(None))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        note_moyenne = await self.get_average_rating(ligne.id)
        requete_nb_avis = select(func.count()).where(
            ServiceReviewModel.id_service == ligne.id,
            ServiceReviewModel.est_approuve.is_(True),
        )
        nb_avis: int = (await self._session.execute(requete_nb_avis)).scalar_one()
        return _svc_to_entity(ligne, avg_rating=note_moyenne, review_count=nb_avis)

    async def get_by_id(self, id_service: int) -> Service | None:
        q = (
            select(ServiceModel)
            .where(ServiceModel.id == id_service, ServiceModel.deleted_at.is_(None))
            .options(
                selectinload(ServiceModel.category),
                selectinload(ServiceModel.galleries),
                selectinload(ServiceModel.packages),
                selectinload(ServiceModel.employees),
            )
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _svc_to_entity(ligne) if ligne else None

    async def create(
        self, id_prestataire: int, id_categorie: int | None, nom: str, identifiant_url: str,
        description: str | None, short_description: str | None, prix: Decimal,
        prix_remise: Decimal | None, duree_minutes: int, est_actif: bool,
        est_mis_en_avant: bool, service_domicile: bool, max_membres: int,
    ) -> Service:
        m = ServiceModel(
            id_prestataire=id_prestataire, id_categorie=id_categorie, nom=nom, identifiant_url=identifiant_url,
            description=description, short_description=short_description, prix=prix,
            prix_remise=prix_remise, duree_minutes=duree_minutes,
            est_actif=est_actif, est_mis_en_avant=est_mis_en_avant, service_domicile=service_domicile,
            max_membres=max_membres,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        # Un service tout juste créé n'a encore ni catégorie chargée ni relations
        # (galeries/forfaits/employés) : les reconstruire ici évite un lazy-load
        # hors contexte async (MissingGreenlet) qu'un refresh() seul ne déclenche pas.
        return Service(
            id=m.id, id_prestataire=m.id_prestataire, id_categorie=m.id_categorie,
            nom=m.nom, identifiant_url=m.identifiant_url, description=m.description,
            short_description=m.short_description, prix=m.prix,
            prix_remise=m.prix_remise, duree_minutes=m.duree_minutes,
            est_actif=m.est_actif, est_mis_en_avant=m.est_mis_en_avant,
            service_domicile=m.service_domicile, max_membres=m.max_membres,
            created_at=m.created_at, updated_at=m.updated_at,
            category=None, galleries=[], packages=[], employees=[],
            note_moyenne=None, review_count=0,
        )

    async def update(
        self, id_service: int, id_prestataire: int | None, id_categorie: int | None,
        nom: str | None, identifiant_url: str | None, description: str | None,
        short_description: str | None, prix: Decimal | None,
        prix_remise: Decimal | None, duree_minutes: int | None,
        est_actif: bool | None, est_mis_en_avant: bool | None, service_domicile: bool | None,
        max_membres: int | None,
    ) -> Service | None:
        q = select(ServiceModel).where(
            ServiceModel.id == id_service, ServiceModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        for attribut, valeur in [
            ("id_prestataire", id_prestataire), ("id_categorie", id_categorie), ("nom", nom),
            ("identifiant_url", identifiant_url), ("description", description), ("short_description", short_description),
            ("prix", prix), ("prix_remise", prix_remise),
            ("duree_minutes", duree_minutes), ("est_actif", est_actif),
            ("est_mis_en_avant", est_mis_en_avant), ("service_domicile", service_domicile),
            ("max_membres", max_membres),
        ]:
            if valeur is not None:
                setattr(ligne, attribut, valeur)
        await self._session.flush()
        await self._session.refresh(ligne)
        return _svc_to_entity(ligne)

    async def soft_delete(self, id_service: int) -> bool:
        q = select(ServiceModel).where(
            ServiceModel.id == id_service, ServiceModel.deleted_at.is_(None)
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True

    async def slug_exists(self, identifiant_url: str, exclude_id: int | None = None) -> bool:
        q = select(func.count()).select_from(ServiceModel).where(
            ServiceModel.identifiant_url == identifiant_url, ServiceModel.deleted_at.is_(None)
        )
        if exclude_id is not None:
            q = q.where(ServiceModel.id != exclude_id)
        return (await self._session.execute(q)).scalar_one() > 0

    async def get_average_rating(self, id_service: int) -> float | None:
        q = select(func.avg(ServiceReviewModel.note)).where(
            ServiceReviewModel.id_service == id_service,
            ServiceReviewModel.est_approuve.is_(True),
        )
        resultat = (await self._session.execute(q)).scalar_one_or_none()
        return float(resultat) if resultat is not None else None


# ---------------------------------------------------------------------------
# ServicePackage
# ---------------------------------------------------------------------------

class SQLAlchemyServicePackageRepository(ServicePackageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, id_service: int) -> list[ServicePackage]:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id_service == id_service,
            ServicePackageModel.deleted_at.is_(None),
        )
        lignes = (await self._session.execute(q)).scalars().all()
        return [_pkg_to_entity(r) for r in lignes]

    async def get_by_id(self, package_id: int) -> ServicePackage | None:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _pkg_to_entity(ligne) if ligne else None

    async def create(
        self, id_service: int, nom: str, description: str | None, prix: Decimal,
        nombre_seances: int, jours_validite: int, est_actif: bool,
    ) -> ServicePackage:
        m = ServicePackageModel(
            id_service=id_service, nom=nom, description=description, prix=prix,
            nombre_seances=nombre_seances, jours_validite=jours_validite, est_actif=est_actif,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _pkg_to_entity(m)

    async def update(
        self, package_id: int, nom: str | None, description: str | None,
        prix: Decimal | None, nombre_seances: int | None, jours_validite: int | None,
        est_actif: bool | None,
    ) -> ServicePackage | None:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return None
        for attribut, valeur in [
            ("nom", nom), ("description", description), ("prix", prix),
            ("nombre_seances", nombre_seances), ("jours_validite", jours_validite),
            ("est_actif", est_actif),
        ]:
            if valeur is not None:
                setattr(ligne, attribut, valeur)
        await self._session.flush()
        await self._session.refresh(ligne)
        return _pkg_to_entity(ligne)

    async def delete(self, package_id: int) -> bool:
        q = select(ServicePackageModel).where(
            ServicePackageModel.id == package_id,
            ServicePackageModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# ServiceEmployee
# ---------------------------------------------------------------------------

class SQLAlchemyServiceEmployeeRepository(ServiceEmployeeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, id_service: int) -> list[ServiceEmployee]:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.id_service == id_service)
        lignes = (await self._session.execute(q)).scalars().all()
        return [_emp_to_entity(r) for r in lignes]

    async def get_by_id(self, employee_id: int) -> ServiceEmployee | None:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.id == employee_id)
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _emp_to_entity(ligne) if ligne else None

    async def assign(self, id_service: int, id_utilisateur: int, est_principal: bool) -> ServiceEmployee:
        m = ServiceEmployeeModel(id_service=id_service, id_utilisateur=id_utilisateur, est_principal=est_principal)
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _emp_to_entity(m)

    async def remove(self, employee_id: int) -> bool:
        q = select(ServiceEmployeeModel).where(ServiceEmployeeModel.id == employee_id)
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        await self._session.delete(ligne)
        await self._session.flush()
        return True


# ---------------------------------------------------------------------------
# ServiceGallery
# ---------------------------------------------------------------------------

class SQLAlchemyServiceGalleryRepository(ServiceGalleryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_service(self, id_service: int) -> list[ServiceGallery]:
        q = select(ServiceGalleryModel).where(
            ServiceGalleryModel.id_service == id_service
        ).order_by(ServiceGalleryModel.ordre_affichage)
        lignes = (await self._session.execute(q)).scalars().all()
        return [_gallery_to_entity(r) for r in lignes]

    async def get_by_id(self, gallery_id: int) -> ServiceGallery | None:
        q = select(ServiceGalleryModel).where(ServiceGalleryModel.id == gallery_id)
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        return _gallery_to_entity(ligne) if ligne else None

    async def add_image(
        self, id_service: int, image: str, legende: str | None, ordre_affichage: int,
    ) -> ServiceGallery:
        m = ServiceGalleryModel(
            id_service=id_service, image=image, legende=legende, ordre_affichage=ordre_affichage
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _gallery_to_entity(m)

    async def delete(self, gallery_id: int) -> bool:
        q = select(ServiceGalleryModel).where(ServiceGalleryModel.id == gallery_id)
        ligne = (await self._session.execute(q)).scalar_one_or_none()
        if ligne is None:
            return False
        await self._session.delete(ligne)
        await self._session.flush()
        return True

    async def reorder(self, items: list[dict]) -> None:
        for item in items:
            await self._session.execute(
                update(ServiceGalleryModel)
                .where(ServiceGalleryModel.id == item["id"])
                .values(ordre_affichage=item["ordre_affichage"])
            )
        await self._session.flush()


# ---------------------------------------------------------------------------
# ServiceReview
# ---------------------------------------------------------------------------

class SQLAlchemyServiceReviewRepository(ServiceReviewRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_approved(
        self, id_service: int, params: PaginationParams
    ) -> tuple[list[ServiceReview], int]:
        requete_base = select(ServiceReviewModel).where(
            ServiceReviewModel.id_service == id_service,
            ServiceReviewModel.est_approuve.is_(True),
        )
        requete_compte = select(func.count()).select_from(requete_base.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()
        requete_lignes = requete_base.order_by(ServiceReviewModel.id.desc()).offset(params.offset).limit(params.per_page)
        lignes = (await self._session.execute(requete_lignes)).scalars().all()
        return [_review_to_entity(r) for r in lignes], total

    async def user_has_review(self, id_service: int, id_utilisateur: int) -> bool:
        q = select(func.count()).select_from(ServiceReviewModel).where(
            ServiceReviewModel.id_service == id_service,
            ServiceReviewModel.id_utilisateur == id_utilisateur,
        )
        return (await self._session.execute(q)).scalar_one() > 0

    async def create(
        self, id_service: int, id_utilisateur: int, note: int, commentaire: str | None,
    ) -> ServiceReview:
        m = ServiceReviewModel(
            id_service=id_service, id_utilisateur=id_utilisateur, note=note,
            commentaire=commentaire, est_approuve=False,
        )
        self._session.add(m)
        await self._session.flush()
        await self._session.refresh(m)
        return _review_to_entity(m)
