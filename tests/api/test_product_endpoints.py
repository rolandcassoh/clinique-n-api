"""Tests API — endpoints catalogue produits."""
import pytest
import pytest_asyncio
from decimal import Decimal
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.shared.exceptions.domain import DomainException

# Import des modèles nécessaires pour créer les tables (ordre important)
import app.modules.auth.infrastructure.models  # noqa: F401 — users table
import app.modules.product.infrastructure.models  # noqa: F401

from app.modules.product.api.router import router as product_router
from app.modules.product.infrastructure.models import (
    BrandModel,
    ProductCategoryModel,
    ProductModel,
)

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)


def _build_app() -> FastAPI:
    app = FastAPI(title="Product Test")
    app.include_router(product_router, prefix="/api")

    @app.exception_handler(DomainException)
    async def _handler(request, exc: DomainException) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    return app


_test_app = _build_app()


@pytest_asyncio.fixture(scope="module", autouse=True)
async def _create_tables():
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    async with _Session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def api_client(db: AsyncSession) -> AsyncClient:
    async def _override():
        yield db

    _test_app.dependency_overrides[get_db] = _override
    async with AsyncClient(
        transport=ASGITransport(app=_test_app), base_url="http://test"
    ) as client:
        yield client
    _test_app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(db: AsyncSession) -> AsyncClient:
    from app.core.auth.jwt_handler import JWTHandler
    from app.core.cache.redis_client import get_redis
    import fakeredis.aioredis as fakeredis

    token = JWTHandler.create_access_token(user_id=1, roles=["client"])
    headers = {"Authorization": f"Bearer {token}"}

    fake_redis_instance = fakeredis.FakeRedis()

    async def _override_db():
        yield db

    async def _override_redis():
        yield fake_redis_instance

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_redis] = _override_redis

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers=headers,
    ) as client:
        yield client
    _test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures de données
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def category(db: AsyncSession) -> ProductCategoryModel:
    from datetime import datetime
    cat = ProductCategoryModel(
        name="Médicaments",
        slug="medicaments",
        parent_id=None,
        image=None,
        description="Tous les médicaments",
        is_active=True,
        sort_order=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(cat)
    await db.flush()
    await db.refresh(cat)
    return cat


@pytest_asyncio.fixture
async def brand(db: AsyncSession) -> BrandModel:
    from datetime import datetime
    b = BrandModel(
        name="Bayer",
        slug="bayer",
        logo=None,
        description=None,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(b)
    await db.flush()
    await db.refresh(b)
    return b


@pytest_asyncio.fixture
async def product(db: AsyncSession, category: ProductCategoryModel) -> ProductModel:
    from datetime import datetime
    p = ProductModel(
        vendor_id=1,
        category_id=category.id,
        brand_id=None,
        unit_id=None,
        name="Aspirine 500mg",
        slug="aspirine-500mg",
        description="Analgésique",
        short_description="Anti-douleur",
        price=Decimal("1500"),
        discount_price=Decimal("1200"),
        stock_quantity=50,
        sku="ASP-500",
        is_active=True,
        is_featured=True,
        weight=None,
        tax_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


# ---------------------------------------------------------------------------
# Tests GET /api/products
# ---------------------------------------------------------------------------


class TestListProducts:
    async def test_returns_200(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/products")
        assert response.status_code == 200

    async def test_returns_paginated_structure(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/products")
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data

    async def test_list_contains_created_product(
        self, api_client: AsyncClient, product: ProductModel
    ) -> None:
        response = await api_client.get("/api/products")
        data = response.json()
        assert data["total"] >= 1
        slugs = [p["slug"] for p in data["data"]]
        assert "aspirine-500mg" in slugs

    async def test_filter_by_is_featured(
        self, api_client: AsyncClient, product: ProductModel
    ) -> None:
        response = await api_client.get("/api/products?is_featured=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_filter_by_category_id(
        self, api_client: AsyncClient, product: ProductModel, category: ProductCategoryModel
    ) -> None:
        response = await api_client.get(f"/api/products?category_id={category.id}")
        assert response.status_code == 200

    async def test_search_filter(
        self, api_client: AsyncClient, product: ProductModel
    ) -> None:
        response = await api_client.get("/api/products?search=Aspirine")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    async def test_pagination(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/products?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert data["per_page"] == 5


# ---------------------------------------------------------------------------
# Tests GET /api/products/{slug}
# ---------------------------------------------------------------------------


class TestGetProduct:
    async def test_existing_product_returns_200(
        self, api_client: AsyncClient, product: ProductModel
    ) -> None:
        response = await api_client.get("/api/products/aspirine-500mg")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "aspirine-500mg"
        assert data["name"] == "Aspirine 500mg"

    async def test_unknown_slug_returns_404(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/products/slug-inexistant")
        assert response.status_code == 404

    async def test_product_has_price_fields(
        self, api_client: AsyncClient, product: ProductModel
    ) -> None:
        response = await api_client.get("/api/products/aspirine-500mg")
        data = response.json()
        assert "price" in data
        assert "discount_price" in data
        assert "stock_quantity" in data


# ---------------------------------------------------------------------------
# Tests GET /api/product-categories
# ---------------------------------------------------------------------------


class TestListCategories:
    async def test_returns_200(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/product-categories")
        assert response.status_code == 200

    async def test_returns_list(self, api_client: AsyncClient) -> None:
        response = await api_client.get("/api/product-categories")
        data = response.json()
        assert isinstance(data, list)

    async def test_contains_created_category(
        self, api_client: AsyncClient, category: ProductCategoryModel
    ) -> None:
        response = await api_client.get("/api/product-categories")
        data = response.json()
        slugs = [c["slug"] for c in data]
        assert "medicaments" in slugs

    async def test_category_has_children_field(
        self, api_client: AsyncClient, category: ProductCategoryModel
    ) -> None:
        response = await api_client.get("/api/product-categories")
        data = response.json()
        assert len(data) > 0
        assert "children" in data[0]

    async def test_nested_category_in_parent(self, api_client: AsyncClient, db: AsyncSession) -> None:
        """Teste l'arbre avec une sous-catégorie."""
        from datetime import datetime
        # Récupère le parent existant
        from sqlalchemy import select
        from app.modules.product.infrastructure.models import ProductCategoryModel as PCM
        result = await db.execute(select(PCM).where(PCM.slug == "medicaments"))
        parent = result.scalar_one_or_none()
        if parent is None:
            pytest.skip("parent category not found")

        child = ProductCategoryModel(
            name="Antibiotiques",
            slug="antibiotiques",
            parent_id=parent.id,
            image=None,
            description=None,
            is_active=True,
            sort_order=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(child)
        await db.flush()

        response = await api_client.get("/api/product-categories")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests GET /api/brands
# ---------------------------------------------------------------------------


class TestListBrands:
    async def test_returns_200(self, api_client: AsyncClient, brand: BrandModel) -> None:
        response = await api_client.get("/api/brands")
        assert response.status_code == 200

    async def test_returns_list(self, api_client: AsyncClient, brand: BrandModel) -> None:
        response = await api_client.get("/api/brands")
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
