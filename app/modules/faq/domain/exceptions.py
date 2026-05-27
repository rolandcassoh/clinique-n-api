"""Exceptions métier du module FAQ."""
from app.shared.exceptions.domain import EntityNotFoundError


class FAQNotFoundError(EntityNotFoundError):
    def __init__(self, faq_id: int) -> None:
        super().__init__("FAQ", faq_id)
