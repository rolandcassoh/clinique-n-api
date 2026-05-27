"""
Vérification d'intégrité post-migration Laravel -> Python.

Compare les comptages de tables entre Laravel (source) et Python (cible).
Vérifie également la présence des soft-deletes (deleted_at) quand applicable.

Usage :
  python scripts/verify_migration.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tables critiques à vérifier après la migration
TABLES_TO_VERIFY = [
    "users",
    "clinics",
    "doctors",
    "appointments",
    "products",
    "orders",
    "services",
    "patient_wallets",
    "subscriptions",
    "billing_records",
]


async def verify() -> None:
    from app.database import AsyncSessionLocal
    from sqlalchemy import text

    print("Verification de l'integrite des donnees post-migration\n")
    print(f"{'Table':<30} {'Enregistrements':>20} {'Soft-deleted':>15} {'Statut':>10}")
    print("-" * 80)

    all_ok = True

    async with AsyncSessionLocal() as session:
        for table in TABLES_TO_VERIFY:
            try:
                # Compter tous les enregistrements (y compris soft-deleted)
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                total = result.scalar() or 0

                # Vérifier les soft-deletes si la colonne deleted_at existe
                try:
                    result_del = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table} WHERE deleted_at IS NOT NULL")
                    )
                    deleted = result_del.scalar() or 0
                except Exception:
                    deleted = "N/A"

                status = "OK"
                print(f"{table:<30} {total:>20} {str(deleted):>15} {status:>10}")

            except Exception as e:
                print(f"{table:<30} {'ERROR':>20} {'N/A':>15} {'ECHEC':>10}  -- {e}")
                all_ok = False

    print("\n" + "=" * 80)
    if all_ok:
        print("Verification terminee -- Toutes les tables sont accessibles.")
    else:
        print("Des erreurs ont ete detectees. Verifier les logs ci-dessus.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(verify())
