"""Implémentations SQLAlchemy asynchrones des repositories blog."""
from datetime import datetime

from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.blog.domain.entites import BlogCategory, BlogPost
from app.modules.blog.domain.depots import BlogCategoryRepository, BlogPostRepository
from app.modules.blog.infrastructure.modeles import BlogCategoryModel, BlogPostModel
from app.shared.schemas.pagination import PaginationParams


def _cat_to_entity(m: BlogCategoryModel) -> BlogCategory:
    return BlogCategory(
        id=m.id,
        nom=m.nom,
        identifiant_url=m.identifiant_url,
        description=m.description,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _post_to_entity(m: BlogPostModel, author_name: str | None = None) -> BlogPost:
    cat_name: str | None = m.category.nom if m.category else None
    return BlogPost(
        id=m.id,
        titre=m.titre,
        identifiant_url=m.identifiant_url,
        extrait=m.extrait,
        contenu=m.contenu,
        id_auteur=m.id_auteur,
        author_name=author_name,
        id_categorie=m.id_categorie,
        category_name=cat_name,
        miniature=m.miniature,
        est_publie=m.est_publie,
        publie_le=m.publie_le,
        vues=m.vues,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class SQLAlchemyBlogCategoryRepository(BlogCategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[BlogCategory]:
        requete = (
            select(BlogCategoryModel)
            .where(BlogCategoryModel.deleted_at.is_(None))
            .order_by(BlogCategoryModel.nom)
        )
        lignes = (await self._session.execute(requete)).scalars().all()
        return [_cat_to_entity(r) for r in lignes]

    async def get_by_slug(self, identifiant_url: str) -> BlogCategory | None:
        requete = select(BlogCategoryModel).where(
            BlogCategoryModel.identifiant_url == identifiant_url,
            BlogCategoryModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        return _cat_to_entity(ligne) if ligne else None


class SQLAlchemyBlogPostRepository(BlogPostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _fetch_author_name(self, id_auteur: int) -> str | None:
        """Récupère le nom de l'auteur depuis la table users."""
        try:
            resultat = await self._session.execute(
                text("SELECT nom FROM users WHERE id = :uid AND deleted_at IS NULL"),
                {"uid": id_auteur},
            )
            ligne = resultat.fetchone()
            return str(ligne[0]) if ligne else None
        except Exception:
            return None

    async def list_published(
        self,
        params: PaginationParams,
        category_slug: str | None = None,
        search: str | None = None,
    ) -> tuple[list[BlogPost], int]:
        base_q = (
            select(BlogPostModel)
            .where(
                BlogPostModel.deleted_at.is_(None),
                BlogPostModel.est_publie.is_(True),
            )
        )
        if category_slug:
            base_q = base_q.join(BlogCategoryModel).where(
                BlogCategoryModel.identifiant_url == category_slug
            )
        if search:
            base_q = base_q.where(
                BlogPostModel.titre.ilike(f"%{search}%")
                | BlogPostModel.extrait.ilike(f"%{search}%")
            )

        requete_compte = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()

        requete_lignes = (
            base_q.order_by(BlogPostModel.publie_le.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        lignes = (await self._session.execute(requete_lignes)).scalars().all()

        articles: list[BlogPost] = []
        for ligne in lignes:
            nom_auteur = await self._fetch_author_name(ligne.id_auteur)
            articles.append(_post_to_entity(ligne, nom_auteur))

        return articles, total

    async def get_by_slug(self, identifiant_url: str) -> BlogPost | None:
        requete = select(BlogPostModel).where(
            BlogPostModel.identifiant_url == identifiant_url,
            BlogPostModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None
        nom_auteur = await self._fetch_author_name(ligne.id_auteur)
        return _post_to_entity(ligne, nom_auteur)

    async def list_all(self, params: PaginationParams) -> tuple[list[BlogPost], int]:
        base_q = select(BlogPostModel).where(BlogPostModel.deleted_at.is_(None))

        requete_compte = select(func.count()).select_from(base_q.subquery())
        total: int = (await self._session.execute(requete_compte)).scalar_one()

        requete_lignes = (
            base_q.order_by(BlogPostModel.id.desc())
            .offset(params.offset)
            .limit(params.per_page)
        )
        lignes = (await self._session.execute(requete_lignes)).scalars().all()

        articles: list[BlogPost] = []
        for ligne in lignes:
            nom_auteur = await self._fetch_author_name(ligne.id_auteur)
            articles.append(_post_to_entity(ligne, nom_auteur))

        return articles, total

    async def increment_views(self, post_id: int) -> None:
        stmt = (
            update(BlogPostModel)
            .where(BlogPostModel.id == post_id)
            .values(vues=BlogPostModel.vues + 1)
        )
        await self._session.execute(stmt)
        await self._session.flush()

    async def create(
        self,
        titre: str,
        identifiant_url: str,
        extrait: str | None,
        contenu: str,
        id_auteur: int,
        id_categorie: int | None,
        miniature: str | None,
        est_publie: bool,
    ) -> BlogPost:
        post = BlogPostModel(
            titre=titre,
            identifiant_url=identifiant_url,
            extrait=extrait,
            contenu=contenu,
            id_auteur=id_auteur,
            id_categorie=id_categorie,
            miniature=miniature,
            est_publie=est_publie,
            publie_le=datetime.utcnow() if est_publie else None,
            vues=0,
        )
        self._session.add(post)
        await self._session.flush()
        await self._session.refresh(post)
        nom_auteur = await self._fetch_author_name(id_auteur)
        return _post_to_entity(post, nom_auteur)

    async def update(
        self,
        post_id: int,
        titre: str | None,
        identifiant_url: str | None,
        extrait: str | None,
        contenu: str | None,
        id_categorie: int | None,
        miniature: str | None,
        est_publie: bool | None,
    ) -> BlogPost | None:
        requete = select(BlogPostModel).where(
            BlogPostModel.id == post_id,
            BlogPostModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return None

        if titre is not None:
            ligne.titre = titre
        if identifiant_url is not None:
            ligne.identifiant_url = identifiant_url
        if extrait is not None:
            ligne.extrait = extrait
        if contenu is not None:
            ligne.contenu = contenu
        if id_categorie is not None:
            ligne.id_categorie = id_categorie
        if miniature is not None:
            ligne.miniature = miniature
        if est_publie is not None:
            etait_publie = ligne.est_publie
            ligne.est_publie = est_publie
            if est_publie and not etait_publie:
                ligne.publie_le = datetime.utcnow()

        await self._session.flush()
        await self._session.refresh(ligne)
        nom_auteur = await self._fetch_author_name(ligne.id_auteur)
        return _post_to_entity(ligne, nom_auteur)

    async def soft_delete(self, post_id: int) -> bool:
        requete = select(BlogPostModel).where(
            BlogPostModel.id == post_id,
            BlogPostModel.deleted_at.is_(None),
        )
        ligne = (await self._session.execute(requete)).scalar_one_or_none()
        if ligne is None:
            return False
        ligne.deleted_at = datetime.utcnow()
        await self._session.flush()
        return True
