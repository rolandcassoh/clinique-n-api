"""Tests unitaires — entités domaine product et value object Money."""
import pytest
from decimal import Decimal

from app.modules.produit.domain.entites import Money, Product, ProductReview


# ---------------------------------------------------------------------------
# Money Value Object
# ---------------------------------------------------------------------------


class TestMoney:
    def test_creation_with_positive_amount(self) -> None:
        m = Money(Decimal("1000"))
        assert m.amount == Decimal("1000")
        assert m.currency == "XAF"

    def test_creation_with_zero(self) -> None:
        m = Money(Decimal("0"))
        assert m.amount == Decimal("0")

    def test_creation_with_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="negative"):
            Money(Decimal("-1"))

    def test_frozen_immutability(self) -> None:
        m = Money(Decimal("500"))
        with pytest.raises(Exception):
            m.amount = Decimal("999")  # type: ignore[misc]

    def test_apply_percentage_discount_10_percent(self) -> None:
        m = Money(Decimal("1000"))
        discounted = m.apply_percentage_discount(Decimal("10"))
        assert discounted.amount == Decimal("900")
        assert discounted.currency == m.currency

    def test_apply_percentage_discount_50_percent(self) -> None:
        m = Money(Decimal("200"))
        discounted = m.apply_percentage_discount(Decimal("50"))
        assert discounted.amount == Decimal("100")

    def test_apply_percentage_discount_0(self) -> None:
        m = Money(Decimal("500"))
        discounted = m.apply_percentage_discount(Decimal("0"))
        assert discounted.amount == Decimal("500")

    def test_apply_percentage_discount_100(self) -> None:
        m = Money(Decimal("500"))
        discounted = m.apply_percentage_discount(Decimal("100"))
        assert discounted.amount == Decimal("0")

    def test_add_same_currency(self) -> None:
        a = Money(Decimal("300"))
        b = Money(Decimal("200"))
        result = a + b
        assert result.amount == Decimal("500")
        assert result.currency == "XAF"

    def test_add_different_currency_raises(self) -> None:
        a = Money(Decimal("300"), "XAF")
        b = Money(Decimal("200"), "EUR")
        with pytest.raises(ValueError, match="currencies"):
            _ = a + b

    def test_multiply(self) -> None:
        m = Money(Decimal("100"))
        result = m * 3
        assert result.amount == Decimal("300")

    def test_multiply_decimal(self) -> None:
        m = Money(Decimal("100"))
        result = m * Decimal("1.5")
        assert result.amount == Decimal("150.0")

    def test_equality_same_values(self) -> None:
        a = Money(Decimal("100"))
        b = Money(Decimal("100"))
        assert a == b

    def test_equality_different_amounts(self) -> None:
        a = Money(Decimal("100"))
        b = Money(Decimal("200"))
        assert a != b


# ---------------------------------------------------------------------------
# Product entity
# ---------------------------------------------------------------------------


def _make_product(
    price: Decimal = Decimal("1000"),
    discount_price: Decimal | None = None,
    stock_quantity: int = 10,
) -> Product:
    return Product(
        id=1,
        vendor_id=1,
        category_id=1,
        brand_id=None,
        unit_id=None,
        name="Aspirine",
        slug="aspirine",
        description=None,
        short_description=None,
        price=price,
        discount_price=discount_price,
        stock_quantity=stock_quantity,
        sku=None,
        is_active=True,
        is_featured=False,
        weight=None,
        tax_id=None,
    )


class TestProductEntity:
    def test_effective_price_no_discount(self) -> None:
        p = _make_product(price=Decimal("1000"))
        assert p.effective_price == Decimal("1000")

    def test_effective_price_with_lower_discount(self) -> None:
        p = _make_product(price=Decimal("1000"), discount_price=Decimal("800"))
        assert p.effective_price == Decimal("800")

    def test_effective_price_discount_higher_than_price(self) -> None:
        # Si discount_price > price, on garde le prix normal
        p = _make_product(price=Decimal("1000"), discount_price=Decimal("1200"))
        assert p.effective_price == Decimal("1000")

    def test_is_in_stock_true(self) -> None:
        p = _make_product(stock_quantity=5)
        assert p.is_in_stock is True

    def test_is_in_stock_false(self) -> None:
        p = _make_product(stock_quantity=0)
        assert p.is_in_stock is False

    def test_has_enough_stock_exact(self) -> None:
        p = _make_product(stock_quantity=5)
        assert p.has_enough_stock(5) is True

    def test_has_enough_stock_insufficient(self) -> None:
        p = _make_product(stock_quantity=3)
        assert p.has_enough_stock(5) is False

    def test_has_enough_stock_zero(self) -> None:
        p = _make_product(stock_quantity=0)
        assert p.has_enough_stock(1) is False

    def test_str_representation(self) -> None:
        p = _make_product()
        assert "aspirine" in str(p)
        assert "Aspirine" in str(p)


# ---------------------------------------------------------------------------
# ProductReview entity
# ---------------------------------------------------------------------------


class TestProductReviewEntity:
    def test_valid_rating_1(self) -> None:
        r = ProductReview(
            id=1, product_id=1, user_id=1, rating=1, comment=None, is_approved=False
        )
        assert r.rating == 1

    def test_valid_rating_5(self) -> None:
        r = ProductReview(
            id=1, product_id=1, user_id=1, rating=5, comment=None, is_approved=False
        )
        assert r.rating == 5

    def test_invalid_rating_0(self) -> None:
        with pytest.raises(ValueError, match="Rating"):
            ProductReview(
                id=1, product_id=1, user_id=1, rating=0, comment=None, is_approved=False
            )

    def test_invalid_rating_6(self) -> None:
        with pytest.raises(ValueError, match="Rating"):
            ProductReview(
                id=1, product_id=1, user_id=1, rating=6, comment=None, is_approved=False
            )
