"""Tests unitaires du domaine world."""
import math
from datetime import datetime

import pytest

from app.modules.monde.domain.entites import City, Country, State
from app.shared.schemas.pagination import Page, PaginationParams


# ---------------------------------------------------------------------------
# Tests des entités
# ---------------------------------------------------------------------------


class TestCountryEntity:
    def test_country_creation(self) -> None:
        country = Country(
            id=1,
            name="France",
            iso2="FR",
            iso3="FRA",
            phone_code="+33",
            capital="Paris",
            currency="EUR",
        )
        assert country.id == 1
        assert country.name == "France"
        assert country.iso2 == "FR"
        assert country.iso3 == "FRA"
        assert country.phone_code == "+33"
        assert country.capital == "Paris"
        assert country.currency == "EUR"

    def test_country_str_representation(self) -> None:
        country = Country(
            id=1, name="France", iso2="FR", iso3="FRA",
            phone_code="+33", capital=None, currency=None,
        )
        assert "FR" in str(country)
        assert "France" in str(country)

    def test_country_optional_fields(self) -> None:
        country = Country(
            id=2, name="TestLand", iso2="TL", iso3="TLN",
            phone_code="000", capital=None, currency=None,
        )
        assert country.capital is None
        assert country.currency is None

    def test_country_timestamps_default(self) -> None:
        before = datetime.now()
        country = Country(
            id=1, name="France", iso2="FR", iso3="FRA",
            phone_code="+33", capital=None, currency=None,
        )
        after = datetime.now()
        assert before <= country.created_at <= after
        assert before <= country.updated_at <= after


class TestStateEntity:
    def test_state_creation(self) -> None:
        state = State(
            id=10, country_id=1, name="Île-de-France", state_code="IDF"
        )
        assert state.id == 10
        assert state.country_id == 1
        assert state.name == "Île-de-France"
        assert state.state_code == "IDF"

    def test_state_str_representation(self) -> None:
        state = State(id=1, country_id=1, name="Bretagne", state_code="BRE")
        result = str(state)
        assert "BRE" in result
        assert "Bretagne" in result


class TestCityEntity:
    def test_city_creation(self) -> None:
        city = City(id=100, state_id=10, name="Paris")
        assert city.id == 100
        assert city.state_id == 10
        assert city.name == "Paris"

    def test_city_str_representation(self) -> None:
        city = City(id=1, state_id=10, name="Lyon")
        assert "Lyon" in str(city)


# ---------------------------------------------------------------------------
# Tests de la pagination
# ---------------------------------------------------------------------------


class TestPaginationParams:
    def test_default_values(self) -> None:
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 20

    def test_offset_first_page(self) -> None:
        params = PaginationParams(page=1, per_page=20)
        assert params.offset == 0

    def test_offset_second_page(self) -> None:
        params = PaginationParams(page=2, per_page=20)
        assert params.offset == 20

    def test_offset_third_page_custom_size(self) -> None:
        params = PaginationParams(page=3, per_page=10)
        assert params.offset == 20

    def test_page_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            PaginationParams(page=0, per_page=20)

    def test_per_page_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            PaginationParams(page=1, per_page=0)

    def test_per_page_max_100(self) -> None:
        with pytest.raises(Exception):
            PaginationParams(page=1, per_page=101)


class TestPageModel:
    def _make_countries(self, n: int) -> list[Country]:
        return [
            Country(
                id=i, name=f"Country {i}", iso2=f"C{i:01d}",
                iso3=f"CT{i:01d}", phone_code=str(i),
                capital=None, currency=None,
            )
            for i in range(1, n + 1)
        ]

    def test_page_create_total_pages(self) -> None:
        params = PaginationParams(page=1, per_page=10)
        items = self._make_countries(10)
        page = Page.create(data=items, total=25, params=params)

        assert page.total == 25
        assert page.page == 1
        assert page.per_page == 10
        assert page.total_pages == 3

    def test_page_create_exact_multiple(self) -> None:
        params = PaginationParams(page=1, per_page=5)
        items = self._make_countries(5)
        page = Page.create(data=items, total=20, params=params)
        assert page.total_pages == 4

    def test_page_create_empty(self) -> None:
        params = PaginationParams(page=1, per_page=20)
        page = Page.create(data=[], total=0, params=params)
        assert page.total_pages == 0
        assert page.data == []

    def test_page_total_pages_ceiling(self) -> None:
        params = PaginationParams(page=1, per_page=10)
        page = Page.create(data=[], total=1, params=params)
        assert page.total_pages == 1

    def test_page_total_pages_calculation(self) -> None:
        for total in range(1, 50):
            for per_page in [5, 10, 20]:
                params = PaginationParams(page=1, per_page=per_page)
                page = Page.create(data=[], total=total, params=params)
                expected = math.ceil(total / per_page)
                assert page.total_pages == expected, (
                    f"total={total}, per_page={per_page}: "
                    f"expected {expected}, got {page.total_pages}"
                )
