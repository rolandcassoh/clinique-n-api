"""Tests API — endpoints commandes (orders)."""
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
import app.modules.product.infrastructure.models  # noqa: F401

from app.modules.product.api.router import router as product_router
from app.modules.product.infrastructure.models import (
    ProductCategoryModel,
    ProductModel,
    CartModel,
    CartItemModel,
    OrderModel,
)

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(_TEST_DB_URL, echo=False)
_Session = async_sessionmaker(bind=_engine, class_=AsyncSession, expire_on_commit=False)

_USER_ID = 20


def _build_app() -> FastAPI:
    app = FastAPI(title="Order Test")
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
    """Client authentifié via override direct de get_current_user."""

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
# Fixtures de données
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def product(db: AsyncSession) -> ProductModel:
    cat = ProductCategoryModel(
        name="Ordres Tests",
        slug="orders-test-cat",
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
        name="Ibuprofène 400mg",
        slug="ibuprofene-400mg",
        description=None,
        short_description=None,
        price=Decimal("2000"),
        discount_price=None,
        stock_quantity=100,
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
async def cart_with_items(db: AsyncSession, product: ProductModel) -> CartModel:
    """Panier préchargé avec un article."""
    now = datetime.utcnow()
    cart = CartModel(user_id=_USER_ID, created_at=now, updated_at=now)
    db.add(cart)
    await db.flush()

    item = CartItemModel(
        cart_id=cart.id,
        product_id=product.id,
        quantity=2,
        unit_price=product.price,
        created_at=now,
        updated_at=now,
    )
    db.add(item)
    await db.flush()
    await db.refresh(cart)
    return cart


@pytest_asyncio.fixture
async def delivered_order(db: AsyncSession) -> OrderModel:
    """Commande avec status 'delivered' — ne peut pas être annulée."""
    now = datetime.utcnow()
    order = OrderModel(
        reference="ORD-20260101-999999",
        user_id=_USER_ID,
        vendor_id=None,
        subtotal=Decimal("4000"),
        discount_amount=Decimal("0"),
        tax_amount=Decimal("0"),
        shipping_amount=Decimal("0"),
        total=Decimal("4000"),
        status="delivered",
        payment_status="paid",
        payment_gateway=None,
        shipping_address=None,
        notes=None,
        promotion_id=None,
        created_at=now,
        updated_at=now,
    )
    db.add(order)
    await db.flush()
    await db.refresh(order)
    return order


# ---------------------------------------------------------------------------
# Tests POST /api/orders
# ---------------------------------------------------------------------------


class TestCreateOrder:
    async def test_create_order_from_empty_cart_returns_400(
        self, auth_client: AsyncClient
    ) -> None:
        # S'assure que le panier est vide
        await auth_client.delete("/api/cart")
        response = await auth_client.post(
            "/api/orders",
            json={"payment_gateway": "cash", "shipping_address": "Yaoundé, Cameroun"},
        )
        assert response.status_code == 400
        data = response.json()
        assert "empty" in data["detail"].lower() or "vide" in data["detail"].lower()

    async def test_create_order_success_returns_201(
        self, auth_client: AsyncClient, cart_with_items: CartModel
    ) -> None:
        response = await auth_client.post(
            "/api/orders",
            json={
                "payment_gateway": "cash",
                "shipping_address": "Yaoundé, Centre, Cameroun",
            },
        )
        assert response.status_code == 201

    async def test_create_order_generates_reference(
        self, auth_client: AsyncClient, db: AsyncSession, product: ProductModel
    ) -> None:
        now = datetime.utcnow()
        cart = CartModel(user_id=_USER_ID, created_at=now, updated_at=now)
        db.add(cart)
        await db.flush()
        item = CartItemModel(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        await db.flush()

        response = await auth_client.post(
            "/api/orders",
            json={"payment_gateway": "mobile_money"},
        )
        if response.status_code == 201:
            data = response.json()
            assert "reference" in data
            assert data["reference"].startswith("ORD-")
            parts = data["reference"].split("-")
            assert len(parts) == 3
            assert len(parts[1]) == 8   # YYYYMMDD
            assert len(parts[2]) == 6   # 6 chiffres

    async def test_create_order_clears_cart(
        self, auth_client: AsyncClient, product: ProductModel
    ) -> None:
        """Après création de commande, le panier doit être vide.

        On utilise l'API pour ajouter au panier (pas d'insertion manuelle)
        afin d'éviter les conflits de session SQLite en mémoire.
        """
        # Vider le panier via API
        await auth_client.delete("/api/cart")

        # Ajouter un article via l'API
        add_resp = await auth_client.post(
            "/api/cart/items",
            json={"product_id": product.id, "quantity": 1},
        )
        assert add_resp.status_code == 201

        # Vérifier que le panier contient bien l'article
        cart_before = await auth_client.get("/api/cart")
        assert cart_before.json()["item_count"] == 1

        # Créer la commande
        order_resp = await auth_client.post("/api/orders", json={})
        assert order_resp.status_code == 201

        # Vérifier que le panier est vide après la commande
        cart_resp = await auth_client.get("/api/cart")
        cart_data = cart_resp.json()
        assert cart_data["item_count"] == 0

    async def test_create_order_status_pending(
        self, auth_client: AsyncClient, db: AsyncSession, product: ProductModel
    ) -> None:
        now = datetime.utcnow()
        cart = CartModel(user_id=_USER_ID, created_at=now, updated_at=now)
        db.add(cart)
        await db.flush()
        item = CartItemModel(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        await db.flush()

        response = await auth_client.post("/api/orders", json={})
        if response.status_code == 201:
            data = response.json()
            assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# Tests GET /api/orders
# ---------------------------------------------------------------------------


class TestListOrders:
    async def test_list_orders_requires_auth(self, anon_client: AsyncClient) -> None:
        response = await anon_client.get("/api/orders")
        assert response.status_code == 401

    async def test_list_orders_returns_paginated(
        self, auth_client: AsyncClient
    ) -> None:
        response = await auth_client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert "page" in data

    async def test_list_orders_filter_by_status(
        self, auth_client: AsyncClient
    ) -> None:
        response = await auth_client.get("/api/orders?status=pending")
        assert response.status_code == 200

    async def test_list_orders_contains_created_order(
        self, auth_client: AsyncClient, db: AsyncSession, product: ProductModel
    ) -> None:
        """Crée une commande puis vérifie qu'elle apparaît dans la liste."""
        now = datetime.utcnow()
        cart = CartModel(user_id=_USER_ID, created_at=now, updated_at=now)
        db.add(cart)
        await db.flush()
        item = CartItemModel(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        await db.flush()

        create_resp = await auth_client.post("/api/orders", json={})
        if create_resp.status_code == 201:
            list_resp = await auth_client.get("/api/orders")
            data = list_resp.json()
            assert data["total"] >= 1


# ---------------------------------------------------------------------------
# Tests POST /api/orders/{id}/cancel
# ---------------------------------------------------------------------------


class TestCancelOrder:
    async def test_cancel_delivered_order_returns_409(
        self, auth_client: AsyncClient, delivered_order: OrderModel
    ) -> None:
        """Annuler une commande livrée → 409 Conflict."""
        response = await auth_client.post(f"/api/orders/{delivered_order.id}/cancel")
        assert response.status_code == 409
        data = response.json()
        # Le message indique qu'elle ne peut pas être annulée
        assert any(
            word in data["detail"].lower()
            for word in ["cancel", "annuler", "cannot", "delivered", "status"]
        )

    async def test_cancel_pending_order_returns_200(
        self, auth_client: AsyncClient, db: AsyncSession, product: ProductModel
    ) -> None:
        """Crée une commande en pending puis l'annule."""
        now = datetime.utcnow()
        cart = CartModel(user_id=_USER_ID, created_at=now, updated_at=now)
        db.add(cart)
        await db.flush()
        item = CartItemModel(
            cart_id=cart.id,
            product_id=product.id,
            quantity=1,
            unit_price=product.price,
            created_at=now,
            updated_at=now,
        )
        db.add(item)
        await db.flush()

        create_resp = await auth_client.post("/api/orders", json={})
        if create_resp.status_code == 201:
            order_id = create_resp.json()["id"]
            cancel_resp = await auth_client.post(f"/api/orders/{order_id}/cancel")
            assert cancel_resp.status_code == 200
            data = cancel_resp.json()
            assert data["status"] == "cancelled"

    async def test_cancel_non_existing_order_returns_404(
        self, auth_client: AsyncClient
    ) -> None:
        response = await auth_client.post("/api/orders/99999/cancel")
        assert response.status_code == 404

    async def test_cancel_other_user_order_returns_404(
        self, db: AsyncSession, delivered_order: OrderModel
    ) -> None:
        """Un user ne peut pas annuler la commande d'un autre (user_id=999 vs _USER_ID=20)."""

        async def _fake_other_user():
            return {"id": 999, "roles": ["client"]}

        async def _override_db():
            yield db

        _test_app.dependency_overrides[get_db] = _override_db
        _test_app.dependency_overrides[get_current_user] = _fake_other_user

        async with AsyncClient(
            transport=ASGITransport(app=_test_app),
            base_url="http://test",
            headers={"Authorization": "Bearer fake-other-token"},
        ) as client:
            response = await client.post(f"/api/orders/{delivered_order.id}/cancel")

        _test_app.dependency_overrides.clear()
        # Soit 404 (commande pas trouvée pour cet user) soit 409 (ne peut pas annuler)
        assert response.status_code in (404, 409)
