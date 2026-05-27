"""
Script de réindexation Meilisearch depuis MySQL.
Usage : python scripts/reindex_search.py --index doctors|products|all
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys

# Ajoute la racine du projet au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def reindex_doctors() -> int:
    """Réindexe tous les médecins depuis la base de données MySQL."""
    from app.database import AsyncSessionLocal
    from app.core.search.meilisearch_client import get_meilisearch_client
    from app.core.search.indexers import DoctorSearchIndexer
    from sqlalchemy import text

    client = get_meilisearch_client()
    if not client:
        print("Meilisearch non disponible — réindexation médecins annulée")
        return 0

    DoctorSearchIndexer.configure(client)

    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT
                d.id,
                u.name,
                d.speciality,
                d.qualification,
                d.experience_years,
                d.consultation_fee,
                d.is_available,
                c.name   AS clinic_name,
                ci.name  AS city_name,
                c.id     AS clinic_id,
                ci.id    AS city_id,
                (d.deleted_at IS NOT NULL) AS is_deleted
            FROM doctors d
            JOIN users   u  ON d.user_id   = u.id
            JOIN clinics c  ON d.clinic_id = c.id
            LEFT JOIN cities ci ON c.city_id = ci.id
            WHERE u.deleted_at IS NULL
        """))
        doctors = [dict(row._mapping) for row in result]

    if doctors:
        client.index(DoctorSearchIndexer.INDEX_NAME).add_documents(doctors)
        print(f"{len(doctors)} médecins indexés")
    else:
        print("Aucun médecin trouvé")
    return len(doctors)


async def reindex_products() -> int:
    """Réindexe tous les produits depuis la base de données MySQL."""
    from app.database import AsyncSessionLocal
    from app.core.search.meilisearch_client import get_meilisearch_client
    from app.core.search.indexers import ProductSearchIndexer
    from sqlalchemy import text

    client = get_meilisearch_client()
    if not client:
        print("Meilisearch non disponible — réindexation produits annulée")
        return 0

    ProductSearchIndexer.configure(client)

    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT
                p.id,
                p.name,
                p.slug,
                p.description,
                p.short_description,
                p.price,
                p.discount_price,
                p.is_active,
                p.is_featured,
                p.sku,
                pc.name AS category_name,
                pc.id   AS category_id,
                b.name  AS brand_name,
                b.id    AS brand_id,
                p.vendor_id,
                (p.deleted_at IS NOT NULL) AS is_deleted
            FROM products p
            LEFT JOIN product_categories pc ON p.category_id = pc.id
            LEFT JOIN brands             b  ON p.brand_id    = b.id
        """))
        products = [dict(row._mapping) for row in result]

    if products:
        client.index(ProductSearchIndexer.INDEX_NAME).add_documents(products)
        print(f"{len(products)} produits indexés")
    else:
        print("Aucun produit trouvé")
    return len(products)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Réindexation Meilisearch depuis MySQL"
    )
    parser.add_argument(
        "--index",
        choices=["doctors", "products", "all"],
        default="all",
        help="Index à réindexer (défaut: all)",
    )
    args = parser.parse_args()

    print(f"Réindexation : {args.index}")
    total = 0
    if args.index in ("doctors", "all"):
        total += await reindex_doctors()
    if args.index in ("products", "all"):
        total += await reindex_products()
    print(f"Réindexation terminée : {total} documents")


if __name__ == "__main__":
    asyncio.run(main())
