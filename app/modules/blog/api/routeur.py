"""Routeur FastAPI du module blog — articles et catégories."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status as statut
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.database import get_db
from app.modules.blog.api.schemas import (
    BlogCategorySchema,
    BlogPostCreateRequest,
    BlogPostDetailSchema,
    BlogPostSchema,
    BlogPostUpdateRequest,
)
from app.modules.blog.application.cas_utilisation import (
    CreateBlogPostUseCase,
    DeleteBlogPostUseCase,
    GetBlogPostBySlugUseCase,
    ListBlogCategoriesUseCase,
    ListPublishedPostsUseCase,
    UpdateBlogPostUseCase,
)
from app.modules.blog.domain.exceptions import (
    BlogPostNotFoundError,
    SlugAlreadyExistsError,
)
from app.modules.blog.infrastructure.depots import (
    SQLAlchemyBlogCategoryRepository,
    SQLAlchemyBlogPostRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Blog - Articles"])

DbDep = Annotated[AsyncSession, Depends(get_db)]
AdminDep = Annotated[dict[str, Any], Depends(require_role("admin", "super-admin"))]


def _cat_repo(db: DbDep) -> SQLAlchemyBlogCategoryRepository:
    return SQLAlchemyBlogCategoryRepository(db)


def _post_repo(db: DbDep) -> SQLAlchemyBlogPostRepository:
    return SQLAlchemyBlogPostRepository(db)


# ---------------------------------------------------------------------------
# Endpoints publics
# ---------------------------------------------------------------------------


@router.get("/blog/categories", response_model=list[BlogCategorySchema])
async def list_blog_categories(
    repo: SQLAlchemyBlogCategoryRepository = Depends(_cat_repo),
) -> list[BlogCategorySchema]:
    """Liste toutes les catégories de blog."""
    uc = ListBlogCategoriesUseCase(repo)
    categories = await uc.execute()
    return [BlogCategorySchema.model_validate(c) for c in categories]


@router.get("/blog/posts", response_model=Page[BlogPostSchema])
async def list_blog_posts(
    category: Annotated[str | None, Query(description="Slug de catégorie")] = None,
    search: Annotated[str | None, Query(description="Recherche dans titre/extrait")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> Page[BlogPostSchema]:
    """Liste paginée des articles publiés."""
    params = PaginationParams(page=page, per_page=per_page)
    uc = ListPublishedPostsUseCase(repo)
    resultat = await uc.execute(params, category, search)
    return resultat  # type: ignore[return-valeur]


@router.get("/blog/posts/{identifiant_url}", response_model=BlogPostDetailSchema)
async def get_blog_post(
    identifiant_url: str,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> BlogPostDetailSchema:
    """Détail d'un article (incrémente les vues)."""
    uc = GetBlogPostBySlugUseCase(repo)
    try:
        article = await uc.execute(identifiant_url)
    except (BlogPostNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(article)


# ---------------------------------------------------------------------------
# Endpoints admin
# ---------------------------------------------------------------------------


@router.post(
    "/admin/blog/posts",
    response_model=BlogPostDetailSchema,
    status_code=statut.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def create_blog_post(
    payload: BlogPostCreateRequest,
    current_user: AdminDep,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> BlogPostDetailSchema:
    """Créer un article de blog (admin)."""
    uc = CreateBlogPostUseCase(repo)
    try:
        article = await uc.execute(
            titre=payload.titre,
            identifiant_url=payload.identifiant_url,
            extrait=payload.extrait,
            contenu=payload.contenu,
            id_auteur=current_user["id"],
            id_categorie=payload.id_categorie,
            miniature=payload.miniature,
            est_publie=payload.est_publie,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=statut.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(article)


@router.put(
    "/admin/blog/posts/{post_id}",
    response_model=BlogPostDetailSchema,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def update_blog_post(
    post_id: int,
    payload: BlogPostUpdateRequest,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> BlogPostDetailSchema:
    """Modifier un article de blog (admin)."""
    uc = UpdateBlogPostUseCase(repo)
    try:
        article = await uc.execute(
            post_id=post_id,
            titre=payload.titre,
            identifiant_url=payload.identifiant_url,
            extrait=payload.extrait,
            contenu=payload.contenu,
            id_categorie=payload.id_categorie,
            miniature=payload.miniature,
            est_publie=payload.est_publie,
        )
    except (BlogPostNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(article)


@router.delete(
    "/admin/blog/posts/{post_id}",
    status_code=statut.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "super-admin"))],
)
async def delete_blog_post(
    post_id: int,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> None:
    """Supprimer (soft delete) un article (admin)."""
    uc = DeleteBlogPostUseCase(repo)
    try:
        await uc.execute(post_id)
    except (BlogPostNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=statut.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
