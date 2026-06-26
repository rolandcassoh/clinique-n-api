"""Exceptions domaine du module product."""
from app.shared.exceptions.domain import DomainException


class ProductNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Produit '{identifier}' introuvable.")


class CategoryNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Catégorie '{identifier}' introuvable.")


class BrandNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Marque '{identifier}' introuvable.")


class InsufficientStockError(DomainException):
    def __init__(self, id_produit: int, requested: int, available: int) -> None:
        super().__init__(
            f"Stock insuffisant pour le produit {id_produit} : "
            f"demandé {requested}, disponible {available}."
        )
        self.id_produit = id_produit
        self.requested = requested
        self.available = available


class CartNotFoundError(DomainException):
    def __init__(self, id_utilisateur: int) -> None:
        super().__init__(f"Panier de l'utilisateur {id_utilisateur} introuvable.")


class CartEmptyError(DomainException):
    def __init__(self) -> None:
        super().__init__("Impossible de créer une commande depuis un panier vide.")


class CartItemNotFoundError(DomainException):
    def __init__(self, id_produit: int) -> None:
        super().__init__(f"Produit {id_produit} introuvable dans le panier.")


class OrderNotFoundError(DomainException):
    def __init__(self, identifier: str | int) -> None:
        super().__init__(f"Commande '{identifier}' introuvable.")


class OrderCannotBeCancelledError(DomainException):
    def __init__(self, id_commande: int, statut: str) -> None:
        super().__init__(
            f"La commande {id_commande} ne peut pas être annulée (statut actuel : {statut})."
        )


class ReviewAlreadyExistsError(DomainException):
    def __init__(self, id_utilisateur: int, id_produit: int) -> None:
        super().__init__(
            f"L'utilisateur {id_utilisateur} a déjà soumis un avis pour le produit {id_produit}."
        )


class ReviewNotFoundError(DomainException):
    def __init__(self, review_id: int) -> None:
        super().__init__(f"Avis {review_id} introuvable.")


class SlugAlreadyExistsError(DomainException):
    def __init__(self, identifiant_url: str) -> None:
        super().__init__(f"Le identifiant_url '{identifiant_url}' existe déjà.")


class WishListItemAlreadyExistsError(DomainException):
    def __init__(self, id_produit: int) -> None:
        super().__init__(f"Le produit {id_produit} est déjà dans la liste de souhaits.")


class WishListItemNotFoundError(DomainException):
    def __init__(self, id_produit: int) -> None:
        super().__init__(f"Produit {id_produit} introuvable dans la liste de souhaits.")
