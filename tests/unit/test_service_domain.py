"""Tests unitaires du domaine Service."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.modules.service.domain.entities import (
    Service,
    ServicePackage,
    ServiceReview,
)
from app.modules.service.domain.exceptions import (
    DuplicateReviewError,
    ServiceNotFoundError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service(**kwargs) -> Service:
    defaults = dict(
        id=1,
        vendor_id=10,
        category_id=None,
        name="Kinésithérapie à domicile",
        slug="kinesitherapie-domicile",
        description="Séances de kiné à domicile.",
        short_description="Kiné à domicile.",
        price=Decimal("50.00"),
        discount_price=None,
        duration_minutes=60,
        is_active=True,
        is_featured=False,
        is_home_service=True,
        max_members=1,
    )
    defaults.update(kwargs)
    return Service(**defaults)


def _make_package(**kwargs) -> ServicePackage:
    defaults = dict(
        id=1,
        service_id=1,
        name="Pack 5 séances",
        description="5 séances de kiné.",
        price=Decimal("220.00"),
        sessions_count=5,
        validity_days=30,
        is_active=True,
        created_at=datetime(2025, 1, 1, 10, 0, 0),
        updated_at=datetime(2025, 1, 1, 10, 0, 0),
    )
    defaults.update(kwargs)
    return ServicePackage(**defaults)


def _make_review(**kwargs) -> ServiceReview:
    defaults = dict(
        id=1,
        service_id=1,
        user_id=42,
        rating=4,
        comment="Très bon service.",
        is_approved=False,
    )
    defaults.update(kwargs)
    return ServiceReview(**defaults)


# ---------------------------------------------------------------------------
# Service entity — effective_price
# ---------------------------------------------------------------------------

class TestServiceEffectivePrice:
    def test_effective_price_without_discount(self) -> None:
        svc = _make_service(price=Decimal("50.00"), discount_price=None)
        assert svc.effective_price == Decimal("50.00")

    def test_effective_price_with_discount(self) -> None:
        svc = _make_service(price=Decimal("50.00"), discount_price=Decimal("35.00"))
        assert svc.effective_price == Decimal("35.00")

    def test_effective_price_zero_discount(self) -> None:
        """discount_price=0 signifie gratuit — pas None."""
        svc = _make_service(price=Decimal("50.00"), discount_price=Decimal("0.00"))
        assert svc.effective_price == Decimal("0.00")

    def test_is_discounted_true_when_discount_set(self) -> None:
        svc = _make_service(price=Decimal("50.00"), discount_price=Decimal("35.00"))
        assert svc.is_discounted is True

    def test_is_discounted_false_when_no_discount(self) -> None:
        svc = _make_service(price=Decimal("50.00"), discount_price=None)
        assert svc.is_discounted is False


# ---------------------------------------------------------------------------
# Service entity — rating_display
# ---------------------------------------------------------------------------

class TestServiceRatingDisplay:
    def test_rating_display_no_reviews(self) -> None:
        svc = _make_service()
        assert svc.average_rating is None
        assert svc.rating_display == "Pas encore noté"

    def test_rating_display_with_average(self) -> None:
        svc = _make_service()
        svc.average_rating = 4.3
        assert "4.3" in svc.rating_display
        assert "5" in svc.rating_display

    def test_rating_display_perfect_score(self) -> None:
        svc = _make_service()
        svc.average_rating = 5.0
        assert "5.0" in svc.rating_display

    def test_rating_display_one_decimal(self) -> None:
        svc = _make_service()
        svc.average_rating = 3.666
        # Doit arrondir à 1 décimale
        assert "3.7" in svc.rating_display


# ---------------------------------------------------------------------------
# Service entity — toggle / activate / deactivate
# ---------------------------------------------------------------------------

class TestServiceActivation:
    def test_deactivate(self) -> None:
        svc = _make_service(is_active=True)
        svc.deactivate()
        assert svc.is_active is False

    def test_activate(self) -> None:
        svc = _make_service(is_active=False)
        svc.activate()
        assert svc.is_active is True

    def test_toggle_active_to_inactive(self) -> None:
        svc = _make_service(is_active=True)
        svc.toggle_active()
        assert svc.is_active is False

    def test_toggle_inactive_to_active(self) -> None:
        svc = _make_service(is_active=False)
        svc.toggle_active()
        assert svc.is_active is True

    def test_str_representation(self) -> None:
        svc = _make_service(id=5, name="Mon service")
        assert "Service" in str(svc)
        assert "5" in str(svc)


# ---------------------------------------------------------------------------
# ServicePackage — validity_end_date
# ---------------------------------------------------------------------------

class TestServicePackageValidityEndDate:
    def test_validity_end_date_30_days(self) -> None:
        from datetime import date
        pkg = _make_package(
            validity_days=30,
            created_at=datetime(2025, 1, 1),
        )
        end = pkg.validity_end_date()
        assert end == date(2025, 1, 31)

    def test_validity_end_date_7_days(self) -> None:
        from datetime import date
        pkg = _make_package(
            validity_days=7,
            created_at=datetime(2025, 3, 1),
        )
        end = pkg.validity_end_date()
        assert end == date(2025, 3, 8)

    def test_validity_end_date_1_day(self) -> None:
        from datetime import date
        pkg = _make_package(
            validity_days=1,
            created_at=datetime(2025, 6, 15),
        )
        end = pkg.validity_end_date()
        assert end == date(2025, 6, 16)

    def test_validity_end_date_365_days(self) -> None:
        from datetime import date
        pkg = _make_package(
            validity_days=365,
            created_at=datetime(2025, 1, 1),
        )
        end = pkg.validity_end_date()
        assert end == date(2026, 1, 1)


# ---------------------------------------------------------------------------
# ServiceReview — unicité user par service
# ---------------------------------------------------------------------------

class TestServiceReviewDomain:
    def test_review_creation_valid_rating(self) -> None:
        review = _make_review(rating=5)
        assert review.rating == 5

    def test_review_min_rating(self) -> None:
        review = _make_review(rating=1)
        assert review.rating == 1

    def test_review_invalid_rating_too_low(self) -> None:
        with pytest.raises(ValueError, match="rating must be between 1 and 5"):
            _make_review(rating=0)

    def test_review_invalid_rating_too_high(self) -> None:
        with pytest.raises(ValueError, match="rating must be between 1 and 5"):
            _make_review(rating=6)

    def test_review_default_not_approved(self) -> None:
        review = _make_review(is_approved=False)
        assert review.is_approved is False

    def test_review_optional_comment(self) -> None:
        review = _make_review(comment=None)
        assert review.comment is None

    def test_duplicate_review_error(self) -> None:
        exc = DuplicateReviewError(user_id=42, service_id=1)
        assert "42" in exc.message
        assert "1" in exc.message

    def test_duplicate_review_error_is_conflict(self) -> None:
        from app.shared.exceptions.domain import ConflictError
        exc = DuplicateReviewError(user_id=1, service_id=2)
        assert isinstance(exc, ConflictError)


# ---------------------------------------------------------------------------
# ServiceNotFoundError
# ---------------------------------------------------------------------------

class TestServiceExceptions:
    def test_service_not_found_by_id(self) -> None:
        exc = ServiceNotFoundError(42)
        assert "42" in str(exc)
        assert "Service" in str(exc)

    def test_service_not_found_by_slug(self) -> None:
        exc = ServiceNotFoundError("mon-slug")
        assert "mon-slug" in str(exc)

    def test_service_not_found_inherits_entity_not_found(self) -> None:
        from app.shared.exceptions.domain import EntityNotFoundError
        exc = ServiceNotFoundError(1)
        assert isinstance(exc, EntityNotFoundError)
