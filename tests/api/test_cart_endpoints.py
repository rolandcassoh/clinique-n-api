"""Tests API — endpoints panier (cart)."""
import pytest
import pytest_asyncio
from decimal import Decimal
from datetime import datetime
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.core.auth.dependencies import get_current_user
from app.shared.exceptions.domain import DomainException

import app.modules.auth.infrastructure.models  # noqa: F401
import app.modules.produit.infrastructure.models  # noqa: F401

from app.modules.produit.api.routeur import router as product_router
from app.modules.produit.infrastructure.modeles import (
    ProductCategoryModel,
    ProductModel,
)

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

_USER_ID = 10


def _build_app() -> FastAPI:
    app = FastAPI(title="Cart Test")
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
async def anon_client(db: AsyncSession) -> AsyncClient:
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
    """Client authentifié — on override get_current_user directement."""

    async def _fake_user():
        return {"id": _USER_ID, "roles": ["client"]}

    async def _override_db():
        yield db

    _test_app.dependency_overrides[get_db] = _override_db
    _test_app.dependency_overrides[get_current_user] = _fake_user

    async with AsyncClient(
        transport=ASGITransport(app=_test_app),
        base_url="http://test",
        headers={"Authorization": "Bearer fake-token"},
    ) as client:
        yield client
    _test_app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixture produit avec stock
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def product_in_stock(db: AsyncSession) -> ProductModel:
    cat = ProductCategoryModel(
        name="Tests",
        slug="tests-cart",
        parent_id=None,
        image=None,
        description=None,
        is_active=True,
        sort_order=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(cat)
    await db.flush()

    p = ProductModel(
        vendor_id=1,
        category_id=cat.id,
        brand_id=None,
        unit_id=None,
        name="Paracétamol 1g",
        slug="paracetamol-1g",
        description=None,
        short_description=None,
        price=Decimal("800"),
        discount_price=None,
        stock_quantity=20,
        sku=None,
        is_active=True,
        is_featured=False,
        weight=None,
        tax_id=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(p)
    await db.flush()
    await db.refresh(p)
    return p


@pytest_asyncio.fixture
async def product_no_stock(db: AsyncSession) -> ProductModel:
    """Produit avec stock = 0."""
    cat = ProductCategoryModel(
        name="Tests2",
        slug="tests-cart-2",
        parent_id=None,
        image=None,
        description=None,
        is_active=True,
        sort_order=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(cat)
    await db.flush()

    p = ProductModel(
        vendor_id=1,
        category_id=cat.id,
        brand_id=None,
        unit_id=None,
        name="Rupture de stock",
        slug="rupture-stock",
        description=None,
        short_description=None,
        price=Decimal("500"),
        discount_price=None,
        stock_quantity=0,
        sku=None,
        is_active=True,
        is_featured=False,
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
# Tests GET /api/cart — authentification requise
# ---------------------------------------------------------------------------


class TestGetCart:
    async def test_get_cart_without_auth_returns_401(self, anon_client: AsyncClient) -> None:
        response = await anon_client.get("/api/cart")
        assert response.status_code == 401

    async def test_get_cart_with_auth_returns_200(self, auth_client: AsyncClient) -> None:
        response = await auth_client.get("/api/cart")
        assert response.status_code == 200

    async def test_get_cart_has_correct_structure(self, auth_client: AsyncClient) -> None:
        response = await auth_client.get("/api/cart")
        data = response.json()
        assert "id" in data
        assert "items" in data
        assert "total" in data
        assert "item_count" in data

    async def test_get_cart_creates_if_not_exists(self, auth_client: AsyncClient) -> None:
        """Premier appel crée le panier automatiquement."""
        response = await auth_client.get("/api/cart")
        assert response.status_code == 200
        data = response.json()
        assert data["item_count"] == 0


# ---------------------------------------------------------------------------
# Tests POST /api/cart/items
# ---------------------------------------------------------------------------


class TestAddToCart:
    async def test_add_item_returns_201(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        # Vider le panier d'abord
        await auth_client.delete("/api/cart")
        response = await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 2},
        )
        assert response.status_code == 201

    async def test_add_item_updates_cart_total(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        await auth_client.delete("/api/cart")
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 1},
        )
        response = await auth_client.get("/api/cart")
        data = response.json()
        assert float(data["total"]) > 0

    async def test_add_item_without_auth_returns_401(
        self, anon_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        response = await anon_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 1},
        )
        assert response.status_code == 401

    async def test_add_item_insufficient_stock_returns_422(
        self, auth_client: AsyncClient, product_no_stock: ProductModel
    ) -> None:
        response = await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_no_stock.id, "quantity": 1},
        )
        assert response.status_code == 422

    async def test_add_item_quantity_exceeds_stock_returns_422(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        """Demander plus que le stock disponible → 422."""
        response = await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 9999},
        )
        assert response.status_code == 422

    async def test_add_same_product_twice_accumulates_quantity(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        """Ajouter 2 fois le même produit → quantités additionnées."""
        await auth_client.delete("/api/cart")

        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 2},
        )
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 3},
        )
        cart_response = await auth_client.get("/api/cart")
        cart = cart_response.json()
        # Un seul item avec quantité 5
        items = cart["items"]
        product_items = [i for i in items if i["product_id"] == product_in_stock.id]
        assert len(product_items) == 1
        assert product_items[0]["quantity"] == 5


# ---------------------------------------------------------------------------
# Tests PATCH /api/cart/items/{product_id}
# ---------------------------------------------------------------------------


class TestUpdateCartItem:
    async def test_update_quantity(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        await auth_client.delete("/api/cart")
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 2},
        )
        response = await auth_client.patch(
            f"/api/cart/items/{product_in_stock.id}",
            json={"quantity": 5},
        )
        assert response.status_code == 200
        data = response.json()
        items = data["items"]
        target = next((i for i in items if i["product_id"] == product_in_stock.id), None)
        assert target is not None
        assert target["quantity"] == 5

    async def test_update_non_existing_item_returns_404(
        self, auth_client: AsyncClient
    ) -> None:
        await auth_client.delete("/api/cart")
        response = await auth_client.patch(
            "/api/cart/items/99999",
            json={"quantity": 2},
        )
        assert response.status_code == 404

    async def test_update_quantity_exceeds_stock_returns_422(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        await auth_client.delete("/api/cart")
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 1},
        )
        response = await auth_client.patch(
            f"/api/cart/items/{product_in_stock.id}",
            json={"quantity": 99999},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests DELETE /api/cart/items/{product_id}
# ---------------------------------------------------------------------------


class TestRemoveFromCart:
    async def test_remove_item(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        await auth_client.delete("/api/cart")
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 1},
        )
        response = await auth_client.delete(f"/api/cart/items/{product_in_stock.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["item_count"] == 0

    async def test_remove_non_existing_item_returns_404(
        self, auth_client: AsyncClient
    ) -> None:
        await auth_client.delete("/api/cart")
        response = await auth_client.delete("/api/cart/items/99999")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Tests DELETE /api/cart
# ---------------------------------------------------------------------------


class TestClearCart:
    async def test_clear_cart(
        self, auth_client: AsyncClient, product_in_stock: ProductModel
    ) -> None:
        await auth_client.post(
            "/api/cart/items",
            json={"product_id": product_in_stock.id, "quantity": 2},
        )
        response = await auth_client.delete("/api/cart")
        assert response.status_code == 200
        data = response.json()
        assert data["item_count"] == 0
        assert float(data["total"]) == 0.0
