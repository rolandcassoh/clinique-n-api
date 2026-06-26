"""Tests unitaires — logique domaine du panier (Cart entity)."""
import pytest
from decimal import Decimal
from datetime import datetime

from app.modules.produit.domain.entites import Cart, CartItem, Product
from app.modules.produit.domain.exceptions import (
    CartItemNotFoundError,
    InsufficientStockError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cart(items: list[CartItem] | None = None) -> Cart:
    return Cart(
        id=1,
        user_id=42,
        items=items or [],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def _make_item(
    product_id: int = 1,
    quantity: int = 2,
    unit_price: Decimal = Decimal("500"),
) -> CartItem:
    return CartItem(
        id=product_id,
        cart_id=1,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
        product_name=f"Product {product_id}",
        product_image=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def _make_product(product_id: int = 1, stock: int = 10, price: Decimal = Decimal("500")) -> Product:
    return Product(
        id=product_id,
        vendor_id=1,
        category_id=1,
        brand_id=None,
        unit_id=None,
        name=f"Product {product_id}",
        slug=f"product-{product_id}",
        description=None,
        short_description=None,
        price=price,
        discount_price=None,
        stock_quantity=stock,
        sku=None,
        is_active=True,
        is_featured=False,
        weight=None,
        tax_id=None,
    )


# ---------------------------------------------------------------------------
# CartItem
# ---------------------------------------------------------------------------


class TestCartItem:
    def test_subtotal_calculation(self) -> None:
        item = _make_item(quantity=3, unit_price=Decimal("200"))
        assert item.subtotal == Decimal("600")

    def test_subtotal_single_item(self) -> None:
        item = _make_item(quantity=1, unit_price=Decimal("1500"))
        assert item.subtotal == Decimal("1500")


# ---------------------------------------------------------------------------
# Cart entity
# ---------------------------------------------------------------------------


class TestCartTotal:
    def test_total_empty_cart(self) -> None:
        cart = _make_cart()
        assert cart.total == Decimal("0")

    def test_total_single_item(self) -> None:
        item = _make_item(quantity=2, unit_price=Decimal("500"))
        cart = _make_cart([item])
        assert cart.total == Decimal("1000")

    def test_total_multiple_items(self) -> None:
        item1 = _make_item(product_id=1, quantity=2, unit_price=Decimal("500"))
        item2 = _make_item(product_id=2, quantity=3, unit_price=Decimal("200"))
        cart = _make_cart([item1, item2])
        # 2*500 + 3*200 = 1000 + 600 = 1600
        assert cart.total == Decimal("1600")

    def test_item_count(self) -> None:
        items = [_make_item(product_id=i) for i in range(1, 4)]
        cart = _make_cart(items)
        assert cart.item_count == 3

    def test_item_count_empty(self) -> None:
        cart = _make_cart()
        assert cart.item_count == 0

    def test_is_empty_true(self) -> None:
        cart = _make_cart()
        assert cart.is_empty() is True

    def test_is_empty_false(self) -> None:
        cart = _make_cart([_make_item()])
        assert cart.is_empty() is False


class TestCartFindItem:
    def test_find_existing_item(self) -> None:
        item = _make_item(product_id=5)
        cart = _make_cart([item])
        found = cart.find_item(5)
        assert found is not None
        assert found.product_id == 5

    def test_find_non_existing_item(self) -> None:
        cart = _make_cart([_make_item(product_id=1)])
        found = cart.find_item(99)
        assert found is None


# ---------------------------------------------------------------------------
# Logique métier d'ajout / vérification de stock (au niveau domaine)
# ---------------------------------------------------------------------------


class TestStockValidation:
    """Tests de la logique de validation stock via les entités domaine."""

    def test_product_sufficient_stock(self) -> None:
        product = _make_product(stock=10)
        assert product.has_enough_stock(5) is True

    def test_product_exact_stock(self) -> None:
        product = _make_product(stock=5)
        assert product.has_enough_stock(5) is True

    def test_product_insufficient_stock_raises_correctly(self) -> None:
        product = _make_product(stock=3)
        # La règle : si stock < quantité → InsufficientStockError doit être levée
        # (levée par le use case, pas directement par l'entité, mais on teste la condition)
        assert product.has_enough_stock(10) is False

    def test_insufficient_stock_error_message(self) -> None:
        error = InsufficientStockError(product_id=1, requested=10, available=3)
        assert "10" in error.message
        assert "3" in error.message
        assert error.product_id == 1

    def test_add_to_cart_cumul_check(self) -> None:
        """Vérifie que le cumul avec un item existant est bien géré."""
        item = _make_item(product_id=1, quantity=3, unit_price=Decimal("500"))
        cart = _make_cart([item])

        product = _make_product(stock=5)
        # Essayer d'ajouter 3 de plus → total 6 > stock 5 → insuffisant
        existing = cart.find_item(1)
        assert existing is not None
        total_requested = existing.quantity + 3
        assert product.has_enough_stock(total_requested) is False

    def test_add_to_cart_cumul_ok(self) -> None:
        """Cumul qui reste dans la limite du stock."""
        item = _make_item(product_id=1, quantity=2, unit_price=Decimal("500"))
        cart = _make_cart([item])

        product = _make_product(stock=5)
        existing = cart.find_item(1)
        assert existing is not None
        total_requested = existing.quantity + 2  # 2 + 2 = 4 <= 5
        assert product.has_enough_stock(total_requested) is True


class TestCartItemNotFoundError:
    def test_error_message(self) -> None:
        err = CartItemNotFoundError(product_id=99)
        assert "99" in err.message
