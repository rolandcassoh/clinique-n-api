#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# Translation mapping for database tables (English -> French)
# Using standard lowercase without accents for robust database table naming
TABLE_MAP = {
    "appointment_patient_bodychart": "schema_corporel_rdv",
    "appointment_transactions": "transactions_rdv",
    "encounter_medical_reports": "rapports_medicaux",
    "encounter_prescriptions": "ordonnances",
    "patient_encounters": "consultations",
    "appointments": "rendez_vous",
    "vital_signs": "signes_vitaux",
    "doctor_clinic_mapping": "correspondance_medecin_clinique",
    "doctor_sessions": "sessions_medecin",
    "doctor_leaves": "conges_medecin",
    "doctor_ratings": "evaluations_medecin",
    "doctor_service_mappings": "services_medecin",
    "clinics_categories": "categories_cliniques",
    "clinic_categories": "categories_cliniques",
    "clinics_services": "services_cliniques",
    "doctors": "medecins",
    "receptionists": "receptionnistes",
    "clinics": "cliniques",
    "personal_access_tokens": "jetons_acces_personnels",
    "model_has_permissions": "modele_a_permissions",
    "role_has_permissions": "role_a_permissions",
    "model_has_roles": "modele_a_roles",
    "user_profiles": "profils_utilisateurs",
    "user_providers": "fournisseurs_utilisateurs",
    "activity_log": "journal_activite",
    "password_resets": "reinitialisations_mots_de_passe",
    "users": "utilisateurs",
    "roles": "roles",
    "subscription_plans": "plans_abonnement",
    "subscriptions_transactions": "transactions_abonnement",
    "commission_earnings": "gains_commissions",
    "employee_commissions": "commissions_employes",
    "employee_earnings": "revenus_employes",
    "billing_records": "factures",
    "billing_items": "lignes_facture",
    "billing_record": "facture",
    "billing_item": "ligne_facture",
    "patient_wallets": "portefeuilles_patients",
    "wallet_histories": "historique_portefeuille",
    "tip_earnings": "pourboires",
    "subscriptions": "abonnements",
    "commissions": "commissions",
    "earnings": "revenus",
    "wallets": "portefeuilles",
    "product_categories": "categories_produits",
    "product_galleries": "galeries_produits",
    "product_variations": "variantes_produits",
    "product_review": "avis_produits",
    "product_tags": "etiquettes_produits",
    "product_tax": "taxes_produits",
    "service_categories": "categories_services",
    "service_packages": "forfaits_services",
    "order_groups": "groupes_commandes",
    "order_items": "articles_commande",
    "order_updates": "mises_a_jour_commande",
    "logistic_zones": "zones_livraison",
    "stock_logs": "journaux_stock",
    "review_galleries": "galeries_avis",
    "requestservices": "demandes_service",
    "products": "produits",
    "brands": "marques",
    "orders": "commandes",
    "wishlist": "liste_souhaits",
    "wish_lists": "listes_souhaits",
    "services": "services",
    "logistics": "logistique",
    "shipping_zones": "zones_livraison",
    "multivendors": "multi_prestataires",
    "incidences": "incidents",
    "modules": "modules",
    "units": "unites",
    "carts": "paniers",
    "notification_templates": "modeles_notifications",
    "bodychart_setting": "parametres_schema_corporel",
    "other_patients": "autres_patients",
    "countries": "pays",
    "states": "regions",
    "cities": "villes",
    "locations": "localisations",
    "addresses": "adresses",
    "notifications": "notifications",
    "holidays": "jours_feries",
    "currencies": "devises",
    "languages": "langues",
    "settings": "parametres",
    "sliders": "diaporamas",
    "blogs": "articles_blog",
    "pages": "pages",
    "tags": "etiquettes",
    "faqs": "faq",
    "media": "medias",
    "migrations": "migrations",
}

BASE_DIR = Path("/home/centenier/centenier/mobile_projects/gestion_clinique/python-api/app")

def refactor_file(file_path: Path):
    content = file_path.read_text(encoding="utf-8")
    original = content

    # 1. Translate __tablename__
    def replace_tablename(match):
        q = match.group(1)
        tbl = match.group(2)
        fr_tbl = TABLE_MAP.get(tbl, tbl)
        return f'__tablename__ = {q}{fr_tbl}{q}'

    content = re.sub(r'__tablename__\s*=\s*(["\'])(.*?)\1', replace_tablename, content)

    # 2. Translate ForeignKey table targets
    # Matches ForeignKey("table_name.id") or ForeignKey('table_name.id')
    def replace_fk(match):
        q = match.group(1)
        tbl = match.group(2)
        rest = match.group(3)
        fr_tbl = TABLE_MAP.get(tbl, tbl)
        return f'ForeignKey({q}{fr_tbl}.{rest}{q}'

    content = re.sub(r'ForeignKey\(\s*(["\'])(.*?)\.(id.*?)\1', replace_fk, content)

    # 3. Remove name="..." parameter from mapped_column calls
    def clean_mapped_column(content_str):
        pos = 0
        while True:
            idx = content_str.find("mapped_column(", pos)
            if idx == -1:
                break
            
            # Find matching parenthesis
            bracket_level = 0
            end_idx = -1
            for i in range(idx + len("mapped_column("), len(content_str)):
                char = content_str[i]
                if char == '(':
                    bracket_level += 1
                elif char == ')':
                    if bracket_level == 0:
                        end_idx = i
                        break
                    else:
                        bracket_level -= 1
            
            if end_idx == -1:
                pos = idx + 1
                continue
            
            args_str = content_str[idx + len("mapped_column("):end_idx]
            
            cleaned_args = []
            bracket_lvl = 0
            current_arg = []
            
            i = 0
            while i < len(args_str):
                char = args_str[i]
                if char == '(':
                    bracket_lvl += 1
                elif char == ')':
                    bracket_lvl -= 1
                
                if char == ',' and bracket_lvl == 0:
                    cleaned_args.append("".join(current_arg))
                    current_arg = []
                else:
                    current_arg.append(char)
                i += 1
            if current_arg:
                cleaned_args.append("".join(current_arg))
            
            filtered_args = []
            for arg in cleaned_args:
                stripped_arg = arg.strip()
                if re.match(r'^name\s*=\s*["\'][a-zA-Z0-9_]+["\']$', stripped_arg):
                    continue
                filtered_args.append(arg)
            
            new_args_str = ",".join(filtered_args)
            
            content_str = content_str[:idx + len("mapped_column(")] + new_args_str + content_str[end_idx:]
            pos = idx + len("mapped_column(") + len(new_args_str) + 1
            
        return content_str

    content = clean_mapped_column(content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"Refactored: {file_path.relative_to(BASE_DIR.parent)}")
        return True
    return False

def main():
    print("Starting refactoring of SQLAlchemy models...")
    count = 0
    for p in BASE_DIR.rglob("modeles.py"):
        if refactor_file(p):
            count += 1
    print(f"Finished refactoring. Modified {count} files.")

if __name__ == "__main__":
    main()
