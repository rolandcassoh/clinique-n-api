"""Tests unitaires du domaine FAQ."""
from datetime import datetime

import pytest

from app.modules.faq.domain.entites import FAQ
from app.modules.faq.domain.exceptions import FAQNotFoundError


class TestFAQEntity:
    def _make_faq(self, **kwargs) -> FAQ:  # type: ignore[no-untyped-def]
        defaults = dict(
            id=1,
            question="Quels sont vos horaires ?",
            answer="Nous sommes ouverts du lundi au vendredi de 8h à 18h.",
            category="Général",
            is_active=True,
            sort_order=0,
        )
        defaults.update(kwargs)
        return FAQ(**defaults)

    def test_faq_creation(self) -> None:
        faq = self._make_faq()
        assert faq.id == 1
        assert faq.question == "Quels sont vos horaires ?"
        assert faq.is_active is True
        assert faq.sort_order == 0

    def test_faq_deactivate(self) -> None:
        faq = self._make_faq(is_active=True)
        faq.deactivate()
        assert faq.is_active is False

    def test_faq_activate(self) -> None:
        faq = self._make_faq(is_active=False)
        faq.activate()
        assert faq.is_active is True

    def test_faq_activate_idempotent(self) -> None:
        faq = self._make_faq(is_active=True)
        faq.activate()
        assert faq.is_active is True

    def test_faq_deactivate_idempotent(self) -> None:
        faq = self._make_faq(is_active=False)
        faq.deactivate()
        assert faq.is_active is False

    def test_faq_optional_category(self) -> None:
        faq = self._make_faq(category=None)
        assert faq.category is None

    def test_faq_timestamps_default(self) -> None:
        before = datetime.now()
        faq = self._make_faq()
        after = datetime.now()
        assert before <= faq.created_at <= after

    def test_faq_str_representation(self) -> None:
        faq = self._make_faq()
        result = str(faq)
        assert "FAQ" in result
        assert "1" in result

    def test_faq_long_question_truncated_in_str(self) -> None:
        long_q = "A" * 100
        faq = self._make_faq(question=long_q)
        # __str__ tronque à 50 chars
        assert len(str(faq)) < len(long_q) + 20

    def test_faq_sort_order_positive(self) -> None:
        faq = self._make_faq(sort_order=5)
        assert faq.sort_order == 5

    def test_faq_sort_order_default(self) -> None:
        faq = self._make_faq()
        assert faq.sort_order == 0


class TestFAQNotFoundError:
    def test_exception_message(self) -> None:
        exc = FAQNotFoundError(42)
        assert "42" in str(exc)
        assert "FAQ" in str(exc)

    def test_exception_inherits_entity_not_found(self) -> None:
        from app.shared.exceptions.domain import EntityNotFoundError
        exc = FAQNotFoundError(1)
        assert isinstance(exc, EntityNotFoundError)

    def test_exception_is_catchable_as_base(self) -> None:
        from app.shared.exceptions.domain import DomainException
        with pytest.raises(DomainException):
            raise FAQNotFoundError(99)
