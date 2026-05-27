"""Exceptions domaine du module product."""
from app.shared.exceptions.domain import DomainException


class ProductNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Product '{identifier}' not found.")


class CategoryNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Category '{identifier}' not found.")


class BrandNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Brand '{identifier}' not found.")


class InsufficientStockError(DomainException):
    def __init__(self, product_id: int, requested: int, available: int) -> None:
        super().__init__(
            f"Insufficient stock for product {product_id}: "
            f"requested {requested}, available {available}."
        )
        self.product_id = product_id
        self.requested = requested
        self.available = available


class CartNotFoundError(DomainException):
    def __init__(self, user_id: int) -> None:
        super().__init__(f"Cart for user {user_id} not found.")


class CartEmptyError(DomainException):
    def __init__(self) -> None:
        super().__init__("Cannot create order from empty cart.")


class CartItemNotFoundError(DomainException):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} not found in cart.")


class OrderNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Order '{identifier}' not found.")


class OrderCannotBeCancelledError(DomainException):
    def __init__(self, order_id: int, status: str) -> None:
        super().__init__(
            f"Order {order_id} cannot be cancelled (current status: {status})."
        )


class ReviewAlreadyExistsError(DomainException):
    def __init__(self, user_id: int, product_id: int) -> None:
        super().__init__(
            f"User {user_id} has already reviewed product {product_id}."
        )


class ReviewNotFoundError(DomainException):
    def __init__(self, review_id: int) -> None:
        super().__init__(f"Review {review_id} not found.")


class SlugAlreadyExistsError(DomainException):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Slug '{slug}' already exists.")


class WishListItemAlreadyExistsError(DomainException):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} is already in wishlist.")


class WishListItemNotFoundError(DomainException):
    def __init__(self, product_id: int) -> None:
        super().__init__(f"Product {product_id} not found in wishlist.")
