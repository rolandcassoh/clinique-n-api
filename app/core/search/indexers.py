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
                "nom", "specialite", "qualification", "clinic_name", "city_name",
            ])
            index.update_filterable_attributes([
                "id_clinique", "id_ville", "specialite", "est_disponible",
                "honoraires_consultation", "is_deleted",
            ])
            index.update_sortable_attributes([
                "honoraires_consultation", "note_moyenne", "annees_experience", "created_at",
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
    def remove_doctor(cls, client, id_medecin: int) -> bool:
        """Supprime un médecin de l'index."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).delete_document(id_medecin)
            return True
        except Exception as exc:
            logger.error("meilisearch.remove_doctor_failed", id_medecin=id_medecin, error=str(exc))
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
            parametres_recherche: dict[str, Any] = {"limit": limit, "offset": offset}

            parties_filtre: list[str] = ["is_deleted = false"]
            if filters:
                for k, v in filters.items():
                    if isinstance(v, str):
                        parties_filtre.append(f"{k} = '{v}'")
                    elif isinstance(v, bool):
                        parties_filtre.append(f"{k} = {str(v).lower()}")
                    else:
                        parties_filtre.append(f"{k} = {v}")
            parametres_recherche["filter"] = " AND ".join(parties_filtre)

            if sort:
                parametres_recherche["sort"] = sort

            resultat = client.index(cls.INDEX_NAME).search(query, parametres_recherche)
            return resultat.get("hits", [])
        except Exception as exc:
            logger.error("meilisearch.recherche_echouee", index=cls.INDEX_NAME, error=str(exc))
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
                "nom", "description", "short_description",
                "category_name", "brand_name", "reference_article",
            ])
            index.update_filterable_attributes([
                "id_categorie", "id_marque", "est_actif", "est_mis_en_avant",
                "is_deleted", "id_prestataire",
            ])
            index.update_sortable_attributes([
                "prix", "prix_remise", "created_at",
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
    def remove_product(cls, client, id_produit: int) -> bool:
        """Supprime un produit de l'index."""
        if not client:
            return False
        try:
            client.index(cls.INDEX_NAME).delete_document(id_produit)
            return True
        except Exception as exc:
            logger.error("meilisearch.remove_product_failed", id_produit=id_produit, error=str(exc))
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
            parametres_recherche: dict[str, Any] = {
                "limit": limit,
                "offset": offset,
            }

            filtre_de_base = "est_actif = true AND is_deleted = false"
            if filters:
                parties_supplementaires: list[str] = []
                for k, v in filters.items():
                    if isinstance(v, str):
                        parties_supplementaires.append(f"{k} = '{v}'")
                    elif isinstance(v, bool):
                        parties_supplementaires.append(f"{k} = {str(v).lower()}")
                    else:
                        parties_supplementaires.append(f"{k} = {v}")
                parametres_recherche["filter"] = filtre_de_base + " AND " + " AND ".join(parties_supplementaires)
            else:
                parametres_recherche["filter"] = filtre_de_base

            if sort:
                parametres_recherche["sort"] = sort

            resultat = client.index(cls.INDEX_NAME).search(query, parametres_recherche)
            return resultat.get("hits", [])
        except Exception as exc:
            logger.error("meilisearch.recherche_produits_echouee", index=cls.INDEX_NAME, error=str(exc))
            return []
