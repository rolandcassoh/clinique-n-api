#!/usr/bin/env python3
"""
Script pour créer des utilisateurs de test dans la base de données.

**OBSOLÈTE / NE FONCTIONNE PAS EN L'ÉTAT (constaté 2026-09-08)** : ce script
importe `Utilisateur, Role` depuis `app.shared.models.base` en supposant des
champs (`mot_de_passe_hash`, `prenom`, une colonne `role=` directe sur
l'utilisateur) qui ne correspondent pas au schéma réel actuel. La table
`utilisateurs` a `mot_de_passe` (pas `mot_de_passe_hash`), pas de `prenom`, et
aucune colonne `role` directe : les rôles passent par la table pivot
polymorphique `modele_a_roles` (voir app/modules/auth/infrastructure/modeles.py
— RoleModel, ModelHasRoleModel, UserModel). Les 5 utilisateurs de test
existent déjà en base (créés on ne sait comment/quand) ; pour leur assigner
des rôles, utiliser scripts/assigner_roles_test.py à la place de la logique de
rôle de ce script.
"""
import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from passlib.context import CryptContext

from app.database import AsyncSessionLocal
from app.shared.models.base import Utilisateur, Role

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hasher un mot de passe"""
    return pwd_context.hash(password)


async def creer_utilisateurs():
    """Créer les utilisateurs de test"""
    
    async with AsyncSessionLocal() as session:
        # Vérifier si les utilisateurs existent déjà
        result = await session.execute(select(Utilisateur).limit(1))
        if result.scalars().first():
            print("⚠️  Des utilisateurs existent déjà dans la base de données")
            reponse = input("Voulez-vous les supprimer et recommencer ? (o/N): ")
            if reponse.lower() != 'o':
                print("❌ Opération annulée")
                return
            
            # Supprimer tous les utilisateurs existants
            await session.execute("DELETE FROM utilisateurs")
            await session.commit()
            print("✓ Utilisateurs existants supprimés")
        
        print("\n🔧 Création des utilisateurs de test...")
        
        # Liste des utilisateurs à créer
        utilisateurs = [
            {
                "email": "admin@clinique-n.com",
                "mot_de_passe": "Admin@2026",
                "nom": "Admin",
                "prenom": "Super",
                "role": Role.SUPER_ADMIN,
                "description": "Super administrateur de la plateforme"
            },
            {
                "email": "admin.clinique@test.com",
                "mot_de_passe": "AdminClinic@2026",
                "nom": "Dupont",
                "prenom": "Jean",
                "role": Role.ADMIN,
                "description": "Administrateur de clinique"
            },
            {
                "email": "medecin@test.com",
                "mot_de_passe": "Medecin@2026",
                "nom": "Martin",
                "prenom": "Sophie",
                "role": Role.MEDECIN,
                "description": "Médecin généraliste"
            },
            {
                "email": "receptionniste@test.com",
                "mot_de_passe": "Reception@2026",
                "nom": "Leblanc",
                "prenom": "Marie",
                "role": Role.RECEPTIONNISTE,
                "description": "Réceptionniste"
            },
            {
                "email": "patient@test.com",
                "mot_de_passe": "Patient@2026",
                "nom": "Bernard",
                "prenom": "Pierre",
                "role": Role.PATIENT,
                "description": "Patient test"
            }
        ]
        
        for data in utilisateurs:
            user = Utilisateur(
                email=data["email"],
                mot_de_passe_hash=hash_password(data["mot_de_passe"]),
                nom=data["nom"],
                prenom=data["prenom"],
                role=data["role"],
                est_actif=True,
                email_verifie=True
            )
            session.add(user)
            print(f"✓ {data['description']}: {data['email']}")
        
        await session.commit()
        
        print("\n" + "="*70)
        print("✅ UTILISATEURS DE TEST CRÉÉS AVEC SUCCÈS")
        print("="*70)
        print("\n📝 IDENTIFIANTS DE CONNEXION:\n")
        
        for data in utilisateurs:
            print(f"🔐 {data['description']}")
            print(f"   Email     : {data['email']}")
            print(f"   Password  : {data['mot_de_passe']}")
            print(f"   Rôle      : {data['role'].value}")
            print()
        
        print("="*70)
        print("\n💡 URLS DE TEST:")
        print("   • API Health:  http://localhost:8000/sante")
        print("   • API Docs:    http://localhost:8000/docs")
        print("   • Login:       http://localhost:8000/api/auth/login")
        print("\n📌 Note: Tous les utilisateurs sont activés et vérifiés")
        print("="*70)


async def main():
    try:
        await creer_utilisateurs()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
