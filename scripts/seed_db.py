"""
Données initiales pour l'environnement de développement.

**OBSOLÈTE / NE FONCTIONNE PAS EN L'ÉTAT (constaté 2026-09-08)** : ce script cible
un schéma anglicisé qui n'existe plus (table `users`, `INSERT INTO roles (name,
guard_name, ...)`, etc.). Le schéma réel utilise `utilisateurs` (colonnes
françaises : `courriel`, `mot_de_passe`, ...), `roles` avec les colonnes
`nom`/`nom_garde`, et la table pivot polymorphique `modele_a_roles`
(`id_role` / `type_modele` / `id_modele`, avec `type_modele =
'App\\Models\\User'`) — voir les modèles ORM dans
app/modules/auth/infrastructure/modeles.py (RoleModel, ModelHasRoleModel,
UserModel). Pour créer/relier des rôles aux utilisateurs de test existants,
utiliser scripts/assigner_roles_test.py à la place. Ce fichier est conservé
tel quel pour référence mais nécessiterait une réécriture complète pour
correspondre au schéma actuel avant de pouvoir être exécuté.

Insère un jeu minimal de données nécessaires pour démarrer :
  - Utilisateurs (admin, médecin, patient)
  - Rôles
  - Pays (Cameroun, France, Sénégal)
  - Devises (XAF, EUR)
  - Langues (fr, en)
  - Plans d'abonnement (Gratuit, Starter, Pro, Enterprise)

Usage :
  python scripts/seed_db.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def seed() -> None:
    from app.database import AsyncSessionLocal, Base, engine
    from sqlalchemy import text

    # Créer les tables si elles n'existent pas encore
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # Vérifier si la base est déjà peuplée
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print(f"Base déjà initialisée ({count} utilisateurs). Aucune action.")
            return

        print("Initialisation de la base de données...")

        # Hash bcrypt pour 'secret' — à remplacer par passlib en production
        password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"

        # ── Utilisateurs initiaux ──────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO users (name, email, password, is_active, created_at, updated_at)
                VALUES
                  ('Super Admin',   'admin@clinique.app',   :pw, 1, NOW(), NOW()),
                  ('Dr. Dupont',    'doctor1@clinique.app', :pw, 1, NOW(), NOW()),
                  ('Patient Test',  'patient1@clinique.app',:pw, 1, NOW(), NOW())
            """),
            {"pw": password_hash},
        )

        # ── Rôles ──────────────────────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO roles (name, guard_name, created_at, updated_at)
                VALUES ('super-admin', 'api', NOW(), NOW()),
                       ('admin',       'api', NOW(), NOW()),
                       ('doctor',      'api', NOW(), NOW()),
                       ('patient',     'api', NOW(), NOW())
                ON DUPLICATE KEY UPDATE name=name
            """)
        )

        # ── Pays ───────────────────────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO countries (name, iso2, iso3, phone_code, created_at, updated_at)
                VALUES ('Cameroun', 'CM', 'CMR', '+237', NOW(), NOW()),
                       ('France',   'FR', 'FRA', '+33',  NOW(), NOW()),
                       ('Sénégal',  'SN', 'SEN', '+221', NOW(), NOW())
                ON DUPLICATE KEY UPDATE name=name
            """)
        )

        # ── Devises ────────────────────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO currencies
                  (name, code, symbol, exchange_rate, is_default, is_active, created_at, updated_at)
                VALUES
                  ('Franc CFA', 'XAF', 'FCFA', 1.000000,   1, 1, NOW(), NOW()),
                  ('Euro',      'EUR', '€',    655.957000,  0, 1, NOW(), NOW())
                ON DUPLICATE KEY UPDATE code=code
            """)
        )

        # ── Langues ────────────────────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO languages
                  (name, code, native_name, is_default, is_active, direction, created_at, updated_at)
                VALUES
                  ('Français', 'fr', 'Français', 1, 1, 'ltr', NOW(), NOW()),
                  ('English',  'en', 'English',  0, 1, 'ltr', NOW(), NOW())
                ON DUPLICATE KEY UPDATE code=code
            """)
        )

        # ── Plans d'abonnement ────────────────────────────────────────────────
        await session.execute(
            text("""
                INSERT INTO subscription_plans
                  (name, slug, description, price, billing_period, trial_days,
                   is_active, is_featured, sort_order, created_at, updated_at)
                VALUES
                  ('Gratuit',    'gratuit',    'Plan de base pour démarrer',          0.00,      'monthly', 0,  1, 0, 1, NOW(), NOW()),
                  ('Starter',    'starter',    'Pour les petites cliniques',          15000.00,  'monthly', 14, 1, 0, 2, NOW(), NOW()),
                  ('Pro',        'pro',        'Pour les cliniques en croissance',    45000.00,  'monthly', 14, 1, 1, 3, NOW(), NOW()),
                  ('Enterprise', 'enterprise', 'Pour les grands établissements',      120000.00, 'yearly',  30, 1, 0, 4, NOW(), NOW())
                ON DUPLICATE KEY UPDATE slug=slug
            """)
        )

        await session.commit()

    print("Initialisation terminée avec succès.")
    print("  -> Utilisateurs : admin@clinique.app / doctor1@clinique.app / patient1@clinique.app")
    print("  -> Mot de passe (dev) : 'secret'")


if __name__ == "__main__":
    asyncio.run(seed())
