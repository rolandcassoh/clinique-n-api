"""Tests d'intégration des endpoints world (countries, states, cities)."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.world.infrastructure.models import CityModel, CountryModel, StateModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _insert_country(db: AsyncSession, name: str = "France", iso2: str = "FR") -> CountryModel:
    country = CountryModel(
        name=name, iso2=iso2, iso3=f"{iso2}A", phone_code="+33", capital="Paris", currency="EUR"
    )
    db.add(country)
    await db.flush()
    await db.refresh(country)
    return country


async def _insert_state(
    db: AsyncSession, country_id: int, name: str = "Île-de-France", code: str = "IDF"
) -> StateModel:
    state = StateModel(country_id=country_id, name=name, state_code=code)
    db.add(state)
    await db.flush()
    await db.refresh(state)
    return state


async def _insert_city(db: AsyncSession, state_id: int, name: str = "Paris") -> CityModel:
    city = CityModel(state_id=state_id, name=name)
    db.add(city)
    await db.flush()
    await db.refresh(city)
    return city


# ---------------------------------------------------------------------------
# Tests GET /api/countries
# ---------------------------------------------------------------------------


class TestListCountries:
    async def test_returns_200(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_country(db)
        resp = await api_client.get("/api/countries")
        assert resp.status_code == 200

    async def test_response_is_paginated(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_country(db, name="Allemagne", iso2="DE")
        resp = await api_client.get("/api/countries")
        body = resp.json()
        assert "data" in body
        assert "total" in body
        assert "page" in body
        assert "per_page" in body
        assert "total_pages" in body

    async def test_search_filters_by_name(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_country(db, name="Espagne", iso2="ES")
        await _insert_country(db, name="Portugal", iso2="PT")

        resp = await api_client.get("/api/countries", params={"search": "Espagne"})
        assert resp.status_code == 200
        body = resp.json()
        names = [c["name"] for c in body["data"]]
        assert "Espagne" in names
        assert "Portugal" not in names

    async def test_search_case_insensitive(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        await _insert_country(db, name="Belgique", iso2="BE")
        resp = await api_client.get("/api/countries", params={"search": "belg"})
        assert resp.status_code == 200
        body = resp.json()
        assert any(c["name"] == "Belgique" for c in body["data"])

    async def test_pagination_params(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        resp = await api_client.get("/api/countries", params={"page": 1, "per_page": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert body["per_page"] == 5
        assert len(body["data"]) <= 5

    async def test_soft_deleted_countries_excluded(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        from datetime import datetime
        country = await _insert_country(db, name="PaysSupp", iso2="PS")
        country.deleted_at = datetime.utcnow()
        await db.flush()

        resp = await api_client.get("/api/countries", params={"search": "PaysSupp"})
        body = resp.json()
        names = [c["name"] for c in body["data"]]
        assert "PaysSupp" not in names


# ---------------------------------------------------------------------------
# Tests GET /api/countries/{id}
# ---------------------------------------------------------------------------


class TestGetCountry:
    async def test_returns_200_with_valid_id(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Italie", iso2="IT")
        resp = await api_client.get(f"/api/countries/{country.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Italie"
        assert body["iso2"] == "IT"

    async def test_returns_404_for_unknown_id(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        resp = await api_client.get("/api/countries/999999")
        assert resp.status_code == 404

    async def test_response_has_all_fields(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Suisse", iso2="CH")
        resp = await api_client.get(f"/api/countries/{country.id}")
        body = resp.json()
        for field in ("id", "name", "iso2", "iso3", "phone_code", "created_at", "updated_at"):
            assert field in body, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Tests GET /api/countries/{id}/states
# ---------------------------------------------------------------------------


class TestListCountryStates:
    async def test_returns_states_for_country(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Maroc", iso2="MA")
        state = await _insert_state(db, country.id, name="Casablanca-Settat", code="CS")

        resp = await api_client.get(f"/api/countries/{country.id}/states")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        names = [s["name"] for s in body]
        assert "Casablanca-Settat" in names

    async def test_returns_404_for_unknown_country(
        self, api_client: AsyncClient
    ) -> None:
        resp = await api_client.get("/api/countries/999999/states")
        assert resp.status_code == 404

    async def test_returns_empty_list_if_no_states(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Micro", iso2="MC")
        resp = await api_client.get(f"/api/countries/{country.id}/states")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# Tests GET /api/states/{id}/cities
# ---------------------------------------------------------------------------


class TestListStateCities:
    async def test_returns_cities_for_state(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Sénégal", iso2="SN")
        state = await _insert_state(db, country.id, name="Dakar", code="DK")
        city = await _insert_city(db, state.id, name="Dakar Plateau")

        resp = await api_client.get(f"/api/states/{state.id}/cities")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Dakar Plateau" in names

    async def test_returns_404_for_unknown_state(
        self, api_client: AsyncClient
    ) -> None:
        resp = await api_client.get("/api/states/999999/cities")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests GET /api/cities
# ---------------------------------------------------------------------------


class TestListCities:
    async def test_returns_200_paginated(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Tunisie", iso2="TN")
        state = await _insert_state(db, country.id, name="Tunis", code="TU")
        await _insert_city(db, state.id, name="Tunis Ville")

        resp = await api_client.get("/api/cities")
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body

    async def test_filter_by_state_id(
        self, api_client: AsyncClient, db: AsyncSession
    ) -> None:
        country = await _insert_country(db, name="Algérie", iso2="DZ")
        state1 = await _insert_state(db, country.id, name="Alger", code="ALG")
        state2 = await _insert_state(db, country.id, name="Oran", code="ORA")
        await _insert_city(db, state1.id, name="Alger Centre")
        await _insert_city(db, state2.id, name="Oran Centre")

        resp = await api_client.get("/api/cities", params={"state_id": state1.id})
        body = resp.json()
        names = [c["name"] for c in body["data"]]
        assert "Alger Centre" in names
        assert "Oran Centre" not in names
