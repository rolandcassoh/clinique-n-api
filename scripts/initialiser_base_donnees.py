#!/usr/bin/env python3
"""
Script d'initialisation de la base de données clinique_dev.
Crée l'utilisateur administrateur par défaut et insère la configuration minimale.
Toutes les chaînes, commentaires et variables sont rédigés en français.
"""
import asyncio
import sys
from pathlib import Path

# Ajouter la racine du projet pour les imports locaux
chemin_racine = Path(__file__).parent.parent
sys.path.insert(0, str(chemin_racine))

from app.core.auth.password import hash_password
from app.database import engine
import asyncmy

async def main():
    print("Connexion à clinique_dev...")
    conn = await asyncmy.connect(
        host="localhost", port=3309, user="root", password="root", db="clinique_dev"
    )
    curseur = conn.cursor()

    # 1. Création de l'utilisateur admin
    mot_de_passe_hache = hash_password("admin123")
    courriel_admin = "admin@clinique.app"
    nom_admin = "Administrateur"
    nom_utilisateur_admin = "admin"
    
    print(f"Création de l'utilisateur par défaut : {nom_admin} ({courriel_admin})...")
    
    # Vérifier si l'utilisateur existe déjà
    await curseur.execute("SELECT id FROM utilisateurs WHERE courriel = %s", (courriel_admin,))
    existe = await curseur.fetchone()
    
    if not existe:
        requete_utilisateur = """
        INSERT INTO utilisateurs (nom, courriel, mot_de_passe, nom_utilisateur, est_actif, totp_actif, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        await curseur.execute(requete_utilisateur, (nom_admin, courriel_admin, mot_de_passe_hache, nom_utilisateur_admin, True, False))
        print("Utilisateur administrateur créé avec succès.")
    else:
        print("L'utilisateur administrateur existe déjà.")

    # 2. Insertion des configurations système indispensables
    configurations = [
        ("theme_mode", "dark", "text", "general", True),
        ("default_time_zone", "Europe/Paris", "text", "general", True),
        ("default_currency", "EUR", "text", "general", True),
        ("app_name", "Gestion Clinique", "text", "general", True),
        ("is_zoom", "0", "boolean", "zoom", True),
        ("razor_payment_method", "0", "boolean", "payment", True),
        ("str_payment_method", "0", "boolean", "payment", True),
    ]

    print("Insertion des configurations indispensables...")
    for cle, valeur, type_valeur, groupe, est_public in configurations:
        # Vérifier si le paramètre existe déjà
        await curseur.execute("SELECT id FROM parametres WHERE cle = %s", (cle,))
        param_existe = await curseur.fetchone()
        
        if not param_existe:
            requete_param = """
            INSERT INTO parametres (cle, valeur, type, groupe, est_public)
            VALUES (%s, %s, %s, %s, %s)
            """
            await curseur.execute(requete_param, (cle, valeur, type_valeur, groupe, est_public))
            print(f"Paramètre '{cle}' inséré.")
        else:
            print(f"Paramètre '{cle}' déjà présent.")

    await conn.commit()
    await conn.ensure_closed()
    print("Initialisation de la base de données terminée.")

if __name__ == "__main__":
    asyncio.run(main())
