"""Router FastAPI du module blog."""
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.modules.blog.application.use_cases import (
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
from app.modules.blog.infrastructure.repositories import (
    SQLAlchemyBlogCategoryRepository,
    SQLAlchemyBlogPostRepository,
)
from app.shared.exceptions.domain import EntityNotFoundError
from app.shared.schemas.pagination import Page, PaginationParams

router = APIRouter(tags=["Blog"])

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
    cats = await uc.execute()
    return [BlogCategorySchema.model_validate(c) for c in cats]


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
    result = await uc.execute(params, category, search)
    return result  # type: ignore[return-value]


@router.get("/blog/posts/{slug}", response_model=BlogPostDetailSchema)
async def get_blog_post(
    slug: str,
    repo: SQLAlchemyBlogPostRepository = Depends(_post_repo),
) -> BlogPostDetailSchema:
    """Détail d'un article (incrémente les vues)."""
    uc = GetBlogPostBySlugUseCase(repo)
    try:
        post = await uc.execute(slug)
    except (BlogPostNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(post)


# ---------------------------------------------------------------------------
# Endpoints admin
# ---------------------------------------------------------------------------


@router.post(
    "/admin/blog/posts",
    response_model=BlogPostDetailSchema,
    status_code=status.HTTP_201_CREATED,
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
        post = await uc.execute(
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            content=payload.content,
            author_id=current_user["id"],
            category_id=payload.category_id,
            thumbnail=payload.thumbnail,
            is_published=payload.is_published,
        )
    except SlugAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(post)


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
        post = await uc.execute(
            post_id=post_id,
            title=payload.title,
            slug=payload.slug,
            excerpt=payload.excerpt,
            content=payload.content,
            category_id=payload.category_id,
            thumbnail=payload.thumbnail,
            is_published=payload.is_published,
        )
    except (BlogPostNotFoundError, EntityNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return BlogPostDetailSchema.model_validate(post)


@router.delete(
    "/admin/blog/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
