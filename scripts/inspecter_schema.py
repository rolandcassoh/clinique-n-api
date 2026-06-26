#!/usr/bin/env python3
"""
Script d'inspection du schéma de la base de données.
Affiche les tables et colonnes définies dans les modèles SQLAlchemy.
"""
import sys
from pathlib import Path

# Ajouter le chemin racine du projet au PATH python
chemin_racine = Path(__file__).parent.parent
sys.path.insert(0, str(chemin_racine))

from app.database import Base

# Importation de tous les modules pour enregistrer les métadonnées
modules_a_importer = [
    "app.modules.client.infrastructure.modeles",
    "app.modules.auth.infrastructure.modeles",
    "app.modules.clinic.infrastructure.modeles",
    "app.modules.consultation.infrastructure.modeles",
    "app.modules.taxe.infrastructure.modeles",
    "app.modules.portefeuille.infrastructure.modeles",
    "app.modules.produit.infrastructure.modeles",
    "app.modules.abonnement.infrastructure.modeles",
    "app.modules.facturation.infrastructure.modeles",
    "app.modules.blog.infrastructure.modeles",
    "app.modules.rendez_vous.infrastructure.modeles",
    "app.modules.promotion.infrastructure.modeles",
    "app.modules.service.infrastructure.modeles",
    "app.modules.monde.infrastructure.modeles",
    "app.modules.page.infrastructure.modeles",
    "app.modules.constante.infrastructure.modeles",
    "app.modules.etiquette.infrastructure.modeles",
    "app.modules.langue.infrastructure.modeles",
    "app.modules.devise.infrastructure.modeles",
    "app.modules.logistique.infrastructure.modeles",
    "app.modules.faq.infrastructure.modeles",
    "app.modules.commission.infrastructure.modeles",
    "app.modules.demande_service.infrastructure.modeles",
    "app.modules.slider.infrastructure.modeles",
    "app.modules.signe_vital.infrastructure.modeles",
]

for nom_module in modules_a_importer:
    __import__(nom_module)

def inspecter_metadonnees():
    print(f"Nombre de tables enregistrées : {len(Base.metadata.tables)}")
    print("-" * 50)
    for nom_table, table_obj in sorted(Base.metadata.tables.items()):
        print(f"Table : {nom_table}")
        colonnes = [col.name for col in table_obj.columns]
        print(f"  Colonnes : {', '.join(colonnes)}")
        print("-" * 50)

if __name__ == "__main__":
    inspecter_metadonnees()
