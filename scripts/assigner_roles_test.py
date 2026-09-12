#!/usr/bin/env python3
"""
Assigne des rôles aux 5 utilisateurs de test existants.

Contexte : les tables `roles` et `modele_a_roles` (pivot polymorphique de
type Laravel-Spatie : id_role / type_modele / id_modele) sont vides alors que
5 utilisateurs de test existent déjà dans `utilisateurs`. La requête de login
(voir app/modules/auth) jointe sur ces deux tables renvoie donc toujours une
liste de rôles vide.

Ce script est idempotent : il peut être relancé sans dupliquer les rôles ni
les liaisons (utilise INSERT ... ON DUPLICATE KEY UPDATE / vérifie l'existence
avant insertion).

Les noms de rôles utilisés correspondent au vocabulaire d'autorisation RÉEL
du backend (voir tous les appels `require_role(...)` sous `app/`) :

    "admin", "super-admin", "doctor", "receptionist" (+ "patient" pour la
    cohérence côté affichage, même si aucun endpoint ne le vérifie).

Une précédente passe avait aligné ces rôles sur l'ancienne énum frontend
('admin' | 'medecin' | 'patient' | 'clinique'), ce qui cassait l'autorisation
backend (ex : medecin@test.com recevait le rôle 'medecin' alors que
require_role("doctor", ...) est utilisé partout côté backend). Le frontend
(frontend/packages/types/src/utilisateur.ts) a été mis à jour en conséquence.

Mapping :
  - admin@clinique-n.com      (Admin Super)   -> super-admin
  - admin.clinique@test.com   (Jean Dupont)    -> admin
  - medecin@test.com          (Sophie Martin)  -> doctor
  - receptionniste@test.com   (Marie Leblanc)  -> receptionist
  - patient@test.com          (Pierre Bernard) -> patient

Ce script est idempotent : relancer supprime toute liaison existante pour ces
utilisateurs vers un rôle différent du rôle cible, puis garantit la liaison
correcte.

Usage :
  python scripts/assigner_roles_test.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.modules.auth.infrastructure.modeles import ModelHasRoleModel, RoleModel

TYPE_MODELE_UTILISATEUR = "App\\Models\\User"

# Rôles à garantir présents dans `roles`.
ROLES = ["admin", "super-admin", "doctor", "receptionist", "patient"]

# email -> nom du rôle à assigner
UTILISATEURS_ROLES = {
    "admin@clinique-n.com": "super-admin",
    "admin.clinique@test.com": "admin",
    "medecin@test.com": "doctor",
    "receptionniste@test.com": "receptionist",
    "patient@test.com": "patient",
}


async def assigner_roles() -> None:
    async with AsyncSessionLocal() as session:
        # 1. Garantir l'existence des rôles
        nom_vers_id: dict[str, int] = {}
        for nom_role in ROLES:
            result = await session.execute(
                select(RoleModel).where(RoleModel.nom == nom_role, RoleModel.nom_garde == "web")
            )
            role = result.scalar_one_or_none()
            if role is None:
                role = RoleModel(nom=nom_role, nom_garde="web")
                session.add(role)
                await session.flush()
                print(f"  + rôle créé : {nom_role} (id={role.id})")
            else:
                print(f"  = rôle déjà présent : {nom_role} (id={role.id})")
            nom_vers_id[nom_role] = role.id

        await session.commit()

        # 2. Récupérer les ids des utilisateurs de test par courriel
        from app.modules.auth.infrastructure.modeles import UserModel

        result = await session.execute(
            select(UserModel).where(UserModel.courriel.in_(UTILISATEURS_ROLES.keys()))
        )
        utilisateurs = {u.courriel: u.id for u in result.scalars().all()}

        manquants = set(UTILISATEURS_ROLES) - set(utilisateurs)
        if manquants:
            print(f"  ! Utilisateurs introuvables (ignorés) : {sorted(manquants)}")

        # 3. Lier chaque utilisateur à son rôle via modele_a_roles (idempotent)
        for courriel, nom_role in UTILISATEURS_ROLES.items():
            if courriel not in utilisateurs:
                continue
            id_utilisateur = utilisateurs[courriel]
            id_role = nom_vers_id[nom_role]

            # Supprimer toute liaison existante vers un AUTRE rôle (nettoyage
            # des anciennes assignations incorrectes, ex : 'medecin'/'clinique').
            suppression = await session.execute(
                delete(ModelHasRoleModel).where(
                    ModelHasRoleModel.type_modele == TYPE_MODELE_UTILISATEUR,
                    ModelHasRoleModel.id_modele == id_utilisateur,
                    ModelHasRoleModel.id_role != id_role,
                )
            )
            if suppression.rowcount:
                print(
                    f"  - {suppression.rowcount} liaison(s) obsolète(s) supprimée(s) pour {courriel}"
                )

            result = await session.execute(
                select(ModelHasRoleModel).where(
                    ModelHasRoleModel.id_role == id_role,
                    ModelHasRoleModel.type_modele == TYPE_MODELE_UTILISATEUR,
                    ModelHasRoleModel.id_modele == id_utilisateur,
                )
            )
            if result.scalar_one_or_none() is not None:
                print(f"  = liaison déjà présente : {courriel} -> {nom_role}")
                continue

            session.add(
                ModelHasRoleModel(
                    id_role=id_role,
                    type_modele=TYPE_MODELE_UTILISATEUR,
                    id_modele=id_utilisateur,
                )
            )
            print(f"  + liaison créée : {courriel} (id={id_utilisateur}) -> {nom_role}")

        await session.commit()
        print("\n✓ Terminé.")


if __name__ == "__main__":
    asyncio.run(assigner_roles())
