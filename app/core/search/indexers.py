"""Indexeurs Meilisearch — Médecins et Produits."""
from __future__ import annotations

from typing import Any, Optional

import structlog

logger = structlog.get_logger()


class DoctorSearchIndexer:
    """Indexeur Meilisearch pour les médecins."""

    INDEX_NAME = "doctors"

    @classmethod
    def configure(cls, client) -> None:
        """Configure les attributs recherchables, filtrables et triables."""
        if not client:
            return
        try:
            index = client.index(cls.INDEX_NAME)
            index.update_searchable_attributes([
                "name", "speciality", "qualification", "clinic_name", "city_name",
            ])
            index.update_filterable_attributes([
                "clinic_id", "city_id", "speciality", "is_available",
                "consultation_fee", "is_deleted",
            ])
            index.update_sortable_attributes([
                "consultation_fee", "average_rating", "experience_years", "created_at",
            ])
            index.update_ranking_rules([
                "words", "typo", "proximity", "attribute", "sort", "exactness",
            ])
            logger.info("meilisearch.doctors_index_configured")
        except Exception as exc:
            logger.error("meilisearch.configure_failed", index=cls.INDEX_NAME, error=str(exc))

    @classmethod
    def index_doctor(cls, client, doctor_data: dict) -> bool:
        """Indexe ou met à jour un médecin."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).add_documents([doctor_data])
            return True
        except Exception as exc:
            logger.error("meilisearch.index_doctor_failed", error=str(exc))
            return False

    @classmethod
    def remove_doctor(cls, client, doctor_id: int) -> bool:
        """Supprime un médecin de l'index."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).delete_document(doctor_id)
            return True
        except Exception as exc:
            logger.error("meilisearch.remove_doctor_failed", doctor_id=doctor_id, error=str(exc))
            return False

    @classmethod
    def search(
        cls,
        client,
        query: str = "",
        filters: Optional[dict] = None,
        sort: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Recherche des médecins dans Meilisearch.
        Exclut automatiquement les médecins supprimés (is_deleted = false).
        """
        if not client:
            return []
        try:
            search_params: dict[str, Any] = {"limit": limit, "offset": offset}

            filter_parts: list[str] = ["is_deleted = false"]
            if filters:
                for k, v in filters.items():
                    if isinstance(v, str):
                        filter_parts.append(f"{k} = '{v}'")
                    elif isinstance(v, bool):
                        filter_parts.append(f"{k} = {str(v).lower()}")
                    else:
                        filter_parts.append(f"{k} = {v}")
            search_params["filter"] = " AND ".join(filter_parts)

            if sort:
                search_params["sort"] = sort

            result = client.index(cls.INDEX_NAME).search(query, search_params)
            return result.get("hits", [])
        except Exception as exc:
            logger.error("meilisearch.search_failed", index=cls.INDEX_NAME, error=str(exc))
            return []


class ProductSearchIndexer:
    """Indexeur Meilisearch pour les produits de la pharmacie/boutique."""

    INDEX_NAME = "products"

    @classmethod
    def configure(cls, client) -> None:
        """Configure les attributs recherchables, filtrables et triables."""
        if not client:
            return
        try:
            index = client.index(cls.INDEX_NAME)
            index.update_searchable_attributes([
                "name", "description", "short_description",
                "category_name", "brand_name", "sku",
            ])
            index.update_filterable_attributes([
                "category_id", "brand_id", "is_active", "is_featured",
                "is_deleted", "vendor_id",
            ])
            index.update_sortable_attributes([
                "price", "discount_price", "created_at",
            ])
            index.update_ranking_rules([
                "words", "typo", "proximity", "attribute", "sort", "exactness",
            ])
            logger.info("meilisearch.products_index_configured")
        except Exception as exc:
            logger.error("meilisearch.configure_products_failed", index=cls.INDEX_NAME, error=str(exc))

    @classmethod
    def index_product(cls, client, product_data: dict) -> bool:
        """Indexe ou met à jour un produit."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).add_documents([product_data])
            return True
        except Exception as exc:
            logger.error("meilisearch.index_product_failed", error=str(exc))
            return False

    @classmethod
    def remove_product(cls, client, product_id: int) -> bool:
        """Supprime un produit de l'index."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).delete_document(product_id)
            return True
        except Exception as exc:
            logger.error("meilisearch.remove_product_failed", product_id=product_id, error=str(exc))
            return False

    @classmethod
    def search(
        cls,
        client,
        query: str = "",
        filters: Optional[dict] = None,
        sort: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Recherche des produits dans Meilisearch.
        N'affiche que les produits actifs et non supprimés.
        """
        if not client:
            return []
        try:
            search_params: dict[str, Any] = {
                "limit": limit,
                "offset": offset,
            }

            base_filter = "is_active = true AND is_deleted = false"
            if filters:
                extra_parts: list[str] = []
                for k, v in filters.items():
                    if isinstance(v, str):
                        extra_parts.append(f"{k} = '{v}'")
                    elif isinstance(v, bool):
                        extra_parts.append(f"{k} = {str(v).lower()}")
                    else:
                        extra_parts.append(f"{k} = {v}")
                search_params["filter"] = base_filter + " AND " + " AND ".join(extra_parts)
            else:
                search_params["filter"] = base_filter

            if sort:
                search_params["sort"] = sort

            result = client.index(cls.INDEX_NAME).search(query, search_params)
            return result.get("hits", [])
        except Exception as exc:
            logger.error("meilisearch.search_products_failed", index=cls.INDEX_NAME, error=str(exc))
            return []
