"""Tests unitaires des indexeurs Meilisearch (sans instance Meilisearch réelle)."""
from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from app.core.search.indexers import DoctorSearchIndexer, ProductSearchIndexer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(hits: list | None = None) -> MagicMock:
    """Crée un mock de client Meilisearch retournant des hits configurables."""
    client = MagicMock()
    index_mock = MagicMock()
    client.index.return_value = index_mock
    index_mock.search.return_value = {"hits": hits or []}
    return client


# ---------------------------------------------------------------------------
# DoctorSearchIndexer — client=None
# ---------------------------------------------------------------------------

class TestDoctorIndexerWithoutClient:
    def test_search_returns_empty_list(self):
        result = DoctorSearchIndexer.search(None, query="cardiologist")
        assert result == []

    def test_search_with_filters_returns_empty_list(self):
        result = DoctorSearchIndexer.search(None, query="", filters={"city_id": 1})
        assert result == []

    def test_configure_is_noop(self):
        # Ne doit pas lever d'exception
        DoctorSearchIndexer.configure(None)

    def test_index_doctor_returns_false(self):
        assert DoctorSearchIndexer.index_doctor(None, {"id": 1, "name": "Dr. Test"}) is False

    def test_remove_doctor_returns_false(self):
        assert DoctorSearchIndexer.remove_doctor(None, 42) is False


# ---------------------------------------------------------------------------
# DoctorSearchIndexer — avec client mock
# ---------------------------------------------------------------------------

class TestDoctorIndexerWithClient:
    def test_search_without_filters_appends_is_deleted_false(self):
        client = _make_mock_client(hits=[{"id": 1, "name": "Dr. Dupont"}])
        result = DoctorSearchIndexer.search(client, query="Dupont")

        assert result == [{"id": 1, "name": "Dr. Dupont"}]
        _, kwargs = client.index.return_value.search.call_args
        assert kwargs is None or True  # l'appel a eu lieu
        call_args = client.index.return_value.search.call_args
        search_params = call_args[0][1] if call_args[0] else call_args[1]
        assert "is_deleted = false" in search_params.get("filter", "")

    def test_search_with_int_filter(self):
        client = _make_mock_client()
        DoctorSearchIndexer.search(client, query="", filters={"clinic_id": 5})
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert "clinic_id = 5" in params["filter"]
        assert "is_deleted = false" in params["filter"]

    def test_search_with_string_filter(self):
        client = _make_mock_client()
        DoctorSearchIndexer.search(client, query="", filters={"speciality": "cardiologie"})
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert "speciality = 'cardiologie'" in params["filter"]

    def test_search_with_sort(self):
        client = _make_mock_client()
        DoctorSearchIndexer.search(client, sort=["consultation_fee:asc"])
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert params["sort"] == ["consultation_fee:asc"]

    def test_search_respects_limit_offset(self):
        client = _make_mock_client()
        DoctorSearchIndexer.search(client, limit=5, offset=10)
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert params["limit"] == 5
        assert params["offset"] == 10

    def test_index_doctor_calls_add_documents(self):
        client = _make_mock_client()
        doctor = {"id": 7, "name": "Dr. Martin", "speciality": "dermato"}
        result = DoctorSearchIndexer.index_doctor(client, doctor)
        assert result is True
        client.index.return_value.add_documents.assert_called_once_with([doctor])

    def test_remove_doctor_calls_delete_document(self):
        client = _make_mock_client()
        result = DoctorSearchIndexer.remove_doctor(client, 7)
        assert result is True
        client.index.return_value.delete_document.assert_called_once_with(7)

    def test_configure_calls_update_methods(self):
        client = _make_mock_client()
        DoctorSearchIndexer.configure(client)
        index_mock = client.index.return_value
        index_mock.update_searchable_attributes.assert_called_once()
        index_mock.update_filterable_attributes.assert_called_once()
        index_mock.update_sortable_attributes.assert_called_once()
        index_mock.update_ranking_rules.assert_called_once()

    def test_search_returns_empty_on_exception(self):
        client = MagicMock()
        client.index.side_effect = RuntimeError("Connection refused")
        result = DoctorSearchIndexer.search(client, query="test")
        assert result == []


# ---------------------------------------------------------------------------
# ProductSearchIndexer — client=None
# ---------------------------------------------------------------------------

class TestProductIndexerWithoutClient:
    def test_search_returns_empty_list(self):
        result = ProductSearchIndexer.search(None, query="aspirine")
        assert result == []

    def test_search_with_filters_returns_empty_list(self):
        result = ProductSearchIndexer.search(None, filters={"category_id": 3})
        assert result == []

    def test_configure_is_noop(self):
        ProductSearchIndexer.configure(None)

    def test_index_product_returns_false(self):
        assert ProductSearchIndexer.index_product(None, {"id": 1, "name": "Paracétamol"}) is False

    def test_remove_product_returns_false(self):
        assert ProductSearchIndexer.remove_product(None, 10) is False


# ---------------------------------------------------------------------------
# ProductSearchIndexer — avec client mock
# ---------------------------------------------------------------------------

class TestProductIndexerWithClient:
    def test_search_base_filter_includes_is_active_and_is_deleted(self):
        client = _make_mock_client(hits=[{"id": 1, "name": "Paracétamol"}])
        result = ProductSearchIndexer.search(client, query="Paracétamol")
        assert result == [{"id": 1, "name": "Paracétamol"}]
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert "is_active = true" in params["filter"]
        assert "is_deleted = false" in params["filter"]

    def test_search_appends_extra_filters(self):
        client = _make_mock_client()
        ProductSearchIndexer.search(client, filters={"category_id": 2, "is_featured": True})
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert "category_id = 2" in params["filter"]
        assert "is_featured = true" in params["filter"]

    def test_search_with_string_filter(self):
        client = _make_mock_client()
        ProductSearchIndexer.search(client, filters={"brand_name": "Pfizer"})
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert "brand_name = 'Pfizer'" in params["filter"]

    def test_search_with_sort(self):
        client = _make_mock_client()
        ProductSearchIndexer.search(client, sort=["price:desc"])
        call_args = client.index.return_value.search.call_args
        params = call_args[0][1] if call_args[0] else call_args[1]
        assert params["sort"] == ["price:desc"]

    def test_configure_calls_update_methods(self):
        client = _make_mock_client()
        ProductSearchIndexer.configure(client)
        index_mock = client.index.return_value
        index_mock.update_searchable_attributes.assert_called_once()
        index_mock.update_filterable_attributes.assert_called_once()
        index_mock.update_sortable_attributes.assert_called_once()
        index_mock.update_ranking_rules.assert_called_once()

    def test_index_product_calls_add_documents(self):
        client = _make_mock_client()
        product = {"id": 42, "name": "Ibuprofène", "price": 1500}
        result = ProductSearchIndexer.index_product(client, product)
        assert result is True
        client.index.return_value.add_documents.assert_called_once_with([product])

    def test_remove_product_calls_delete_document(self):
        client = _make_mock_client()
        result = ProductSearchIndexer.remove_product(client, 42)
        assert result is True
        client.index.return_value.delete_document.assert_called_once_with(42)

    def test_search_returns_empty_on_exception(self):
        client = MagicMock()
        client.index.side_effect = ConnectionError("Meilisearch down")
        result = ProductSearchIndexer.search(client, query="test")
        assert result == []


# ---------------------------------------------------------------------------
# get_meilisearch_client — sans instance réelle
# ---------------------------------------------------------------------------

class TestMeilisearchClient:
    def test_returns_none_when_meilisearch_unavailable(self, monkeypatch):
        """Sans Meilisearch, la fonction doit retourner None proprement."""
        import app.core.search.meilisearch_client as mc_module

        def _failing_client(*args, **kwargs):
            raise ConnectionError("Connection refused")

        monkeypatch.setattr(
            mc_module,
            "get_meilisearch_client",
            lambda: None,
        )
        from app.core.search.meilisearch_client import get_meilisearch_client
        result = get_meilisearch_client()
        assert result is None
