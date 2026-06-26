#!/usr/bin/env python3
"""
Script de migration et de traduction des données de clinique_en vers clinique_dev.
Toutes les chaînes de texte utilisateur (descriptions, diagnostics, ordonnances, etc.)
sont traduites en français.
"""
import asyncio
import time
import sys
import json
from pathlib import Path
from decimal import Decimal

# Ajouter le chemin racine au PATH python
chemin_racine = Path(__file__).parent.parent
sys.path.insert(0, str(chemin_racine))

import asyncmy
from deep_translator import GoogleTranslator

# Table de correspondance des tables (Anglais -> Français)
CORRESPONDANCE_TABLES = {
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

# Table de correspondance par défaut des colonnes (Anglais -> Français)
CORRESPONDANCE_COLONNES = {
    "name": "nom",
    "email": "courriel",
    "password": "mot_de_passe",
    "username": "nom_utilisateur",
    "phone": "telephone",
    "is_active": "est_actif",
    "email_verified_at": "courriel_verifie_le",
    "otp_code": "code_otp",
    "totp_secret": "secret_totp",
    "totp_enabled": "totp_actif",
    "guard_name": "nom_garde",
    "token": "jeton",
    "token_type": "type_jeton",
    "expires_at": "expire_le",
    "last_used_at": "derniere_utilisation_le",
    "is_revoked": "est_revoque",
    "avatar": "avatar",
    "address": "adresse",
    "city_id": "id_ville",
    "date_of_birth": "date_naissance",
    "gender": "sexe",
    "blood_group": "groupe_sanguin",
    "bio": "biographie",
    "user_id": "id_utilisateur",
    "owner_id": "id_proprietaire",
    "slug": "identifiant_url",
    "website": "site_web",
    "cover_image": "image_couverture",
    "commission_rate": "taux_commission",
    "clinic_id": "id_clinique",
    "price": "prix",
    "duration_minutes": "duree_minutes",
    "doctor_id": "id_medecin",
    "speciality": "specialite",
    "experience_years": "annees_experience",
    "consultation_fee": "honoraires_consultation",
    "advance_payment_amount": "montant_avance",
    "is_available": "est_disponible",
    "google_calendar_id": "id_agenda_google",
    "average_rating": "note_moyenne",
    "day_of_week": "jour_semaine",
    "start_time": "heure_debut",
    "end_time": "heure_fin",
    "slot_duration_minutes": "duree_creneau_minutes",
    "max_patients_per_slot": "max_patients_par_creneau",
    "leave_date": "date_absence",
    "reason": "motif",
    "is_full_day": "journee_complete",
    "rating": "note",
    "comment": "commentaire",
    "is_approved": "est_approuve",
    "patient_id": "id_patient",
    "reference": "reference",
    "scheduled_at": "programme_le",
    "payment_status": "statut_paiement",
    "payment_gateway": "passerelle_paiement",
    "payment_reference": "reference_paiement",
    "status": "statut",
    "notes": "notes",
    "cancellation_reason": "motif_annulation",
    "amount": "montant",
    "currency": "devise",
    "gateway_response": "reponse_passerelle",
    "transaction_ref": "reference_transaction",
    "is_followup": "est_suivi",
    "advance_amount": "montant_avance",
    "appointment_id": "id_rendez_vous",
    "encounter_id": "id_consultation",
    "chief_complaint": "motif_principal",
    "encounter_date": "date_consultation",
    "follow_up_date": "date_suivi",
    "follow_up_notes": "notes_suivi",
    "symptoms": "symptomes",
    "diagnosis": "diagnostic",
    "treatment": "traitement",
    "blood_pressure": "tension_arterielle",
    "temperature": "temperature",
    "weight": "poids",
    "additional_notes": "notes_complementaires",
    "medication_name": "nom_medicament",
    "dosage": "posologie",
    "frequency": "frequence",
    "duration_days": "duree_jours",
    "instructions": "instructions",
    "is_chronic": "est_chronique",
    "image_url": "url_image",
    "recorded_by": "enregistre_par",
    "blood_pressure_systolic": "tension_systolique",
    "blood_pressure_diastolic": "tension_diastolique",
    "heart_rate": "frequence_cardiaque",
    "oxygen_saturation": "saturation_oxygene",
    "blood_sugar": "glycemie",
    "height": "taille",
    "recorded_at": "enregistre_le",
    "billing_id": "id_facture",
    "subtotal": "sous_total",
    "discount_amount": "montant_remise",
    "tax_amount": "montant_taxe",
    "total": "total",
    "due_date": "date_echeance",
    "paid_at": "paye_le",
    "quantity": "quantite",
    "unit_price": "prix_unitaire",
    "tax_rate": "taux_taxe",
    "wallet_id": "id_portefeuille",
    "balance": "solde",
    "balance_after": "solde_apres",
    "commission_amount": "montant_commission",
    "doctor_earning": "gain_medecin",
    "appointment_amount": "montant_rdv",
    "period_start": "debut_periode",
    "period_end": "fin_periode",
    "total_appointments": "total_rdv",
    "gross_amount": "montant_brut",
    "commission_deducted": "commission_deduite",
    "net_amount": "montant_net",
    "plan_id": "id_plan",
    "billing_period": "periode_facturation",
    "trial_days": "jours_essai",
    "feature": "fonctionnalite",
    "value": "valeur",
    "start_date": "date_debut",
    "starts_at": "debut_le",
    "end_date": "date_fin",
    "ends_at": "fin_le",
    "cancelled_at": "annule_le",
    "auto_renew": "renouvellement_auto",
    "is_trial": "est_essai",
    "category_id": "id_categorie",
    "sort_order": "ordre_affichage",
    "is_featured": "est_mis_en_avant",
    "is_home_service": "service_domicile",
    "max_members": "max_membres",
    "sessions_count": "nombre_seances",
    "validity_days": "jours_validite",
    "is_primary": "est_principal",
    "caption": "legende",
    "parent_id": "id_rdv_parent",
    "google_event_id": "id_evenement_google",
    "rate": "tarif",
    "is_default": "est_defaut",
    "abbreviation": "abreviation",
    "abréviation": "abreviation",
    "country_id": "id_pays",
    "state_id": "id_region",
    "title": "titre",
    "subtitle": "sous_titre",
    "link": "lien",
    "button_text": "texte_bouton",
    "iso2": "code_iso2",
    "iso3": "code_iso3",
    "phonecode": "indicatif_telephone",
    "capital": "capitale",
    "meta_title": "titre_meta",
    "is_published": "est_publie",
    "fcode": "code_region",
    "brand_id": "id_marque",
    "unit_id": "id_unite",
    "short_description": "short_description",
    "qty": "quantite_stock",
    "sku": "reference_article",
    "wish_list_id": "id_liste_souhaits",
    "product_id": "id_produit",
    "coupon_id": "id_promotion",
    "order_id": "id_commande",
    "use_date": "utilise_le",
    "min_order_amount": "montant_min_commande",
    "max_discount": "remise_maximale",
    "usage_limit": "limite_utilisation",
    "usage_count": "compteur_utilisation",
    "used_at": "utilise_le",
    "start_at": "debut_le",
    "end_at": "expire_le",
    "applicable_on": "applicable_a",
    "budget_min": "budget_min",
    "budget_max": "budget_max",
    "preferred_date": "preferred_date",
    "preferred_slot": "creneau_prefere",
    "shipping_rate": "tarif",
    "min_weight": "poids_min",
    "max_weight": "poids_max",
    "min_order_total": "montant_min_commande",
    "free_shipping": "livraison_gratuite",
    "min_delivery_days": "jours_livraison_min",
    "max_delivery_days": "jours_livraison_max",
    "zone_id": "id_zone",
}

# Colonnes contenant du texte à traduire en français
COLONNES_A_TRADUIRE = {
    "description", "bio", "biographie", "notes", "additional_notes", 
    "notes_complementaires", "notes_suivi", "follow_up_notes",
    "chief_complaint", "motif_principal", "symptoms", "symptomes",
    "diagnosis", "diagnostic", "treatment", "traitement",
    "instructions", "motif", "reason", "comment", "commentaire",
    "speciality", "specialite", "qualification", "medication_name", 
    "nom_medicament", "item_name", "title", "titre", "subtitle", 
    "sous_titre", "button_text", "texte_bouton", "content", "contenu",
    "short_description", "nom"
}

# Initialiser le traducteur Google
traducteur = GoogleTranslator(source="en", target="fr")

def traduire_valeur(texte: str, nom_colonne: str, nom_table_src: str) -> str:
    """
    Traduit une chaîne de caractères de l'anglais vers le français si nécessaire.
    """
    if not text_is_valid_for_translation(texte):
        return texte
        
    # Ne pas traduire les noms propres (tables géographiques, marques)
    if nom_table_src in ("cities", "states", "countries", "brands", "locations", "addresses"):
        return texte

    # Ne pas traduire les noms d'utilisateurs (noms propres)
    if nom_table_src == "users" and nom_colonne == "nom":
        return texte

    # Ne traduire que si la colonne fait partie des cibles de traduction
    if nom_colonne in COLONNES_A_TRADUIRE:
        try:
            # Petite pause pour respecter les limites d'appels API
            time.sleep(0.04)
            texte_traduit = traducteur.translate(texte)
            print(f"Traduction [{nom_table_src}.{nom_colonne}] : '{texte}' -> '{texte_traduit}'")
            return texte_traduit
        except Exception as e:
            print(f"Échec de traduction pour '{texte}': {e}")
            return texte
            
    return texte

def text_is_valid_for_translation(texte):
    if not texte or not isinstance(texte, str):
        return False
    # Ne pas traduire les URLs, les adresses e-mail ou les clés
    if texte.startswith("http://") or texte.startswith("https://") or "@" in texte:
        return False
    # Si le texte est très court (ex: code de devise, numéro, etc.), on ne le traduit pas
    if len(texte.strip()) <= 3 and not texte.isalpha():
        return False
    return True

async def recuperer_colonnes(curseur, nom_table: str, nom_base: str) -> list[str]:
    """Retourne la liste des colonnes d'une table."""
    await curseur.execute(f"SHOW COLUMNS FROM {nom_base}.{nom_table}")
    res = await curseur.fetchall()
    return [colonne[0] for colonne in res]

async def main():
    print("Connexion aux bases de données MySQL...")
    # Connexion à clinique_en
    conn_en = await asyncmy.connect(
        host="localhost", port=3309, user="root", password="root", db="clinique_en"
    )
    # Connexion à clinique_dev
    conn_dev = await asyncmy.connect(
        host="localhost", port=3309, user="root", password="root", db="clinique_dev"
    )

    curseur_en = conn_en.cursor()
    curseur_dev = conn_dev.cursor()

    # Désactiver les vérifications des clés étrangères pour insérer sans blocage
    await curseur_dev.execute("SET FOREIGN_KEY_CHECKS = 0;")
    print("Vérification des clés étrangères désactivée dans clinique_dev.")

    # Récupérer toutes les tables de la base source
    await curseur_en.execute("SHOW TABLES FROM clinique_en")
    tables_src = [t[0] for t in await curseur_en.fetchall()]

    for table_src in sorted(tables_src):
        # Déterminer le nom de la table cible
        table_cible = CORRESPONDANCE_TABLES.get(table_src, table_src)

        # Vérifier si la table cible existe dans clinique_dev
        try:
            await curseur_dev.execute(f"SHOW COLUMNS FROM clinique_dev.{table_cible}")
            await curseur_dev.fetchall()
        except Exception:
            # Si la table n'existe pas, on passe à la suivante
            print(f"Table cible '{table_cible}' absente dans clinique_dev. Ignorée.")
            continue

        print(f"Migration de la table : {table_src} -> {table_cible}...")

        # Récupérer les colonnes de la table source et cible
        colonnes_src = await recuperer_colonnes(curseur_en, table_src, "clinique_en")
        colonnes_cible = await recuperer_colonnes(curseur_dev, table_cible, "clinique_dev")

        # Lire toutes les lignes de la table source
        await curseur_en.execute(f"SELECT * FROM clinique_en.{table_src}")
        lignes = await curseur_en.fetchall()

        if not lignes:
            print(f"Table {table_src} vide.")
            continue

        print(f"  Transfert et traduction de {len(lignes)} enregistrements...")

        lignes_a_inserer = []
        for ligne in lignes:
            valeurs_cible = []
            ligne_dict = dict(zip(colonnes_src, ligne))
            
            # Traitements spécifiques pour adapter la structure de la source à la cible
            if table_src == "users":
                nom_complet = f"{ligne_dict.get('first_name', '')} {ligne_dict.get('last_name', '')}".strip()
                ligne_dict["nom"] = nom_complet if nom_complet else "Utilisateur"
                ligne_dict["courriel"] = ligne_dict.get("email")
                if not ligne_dict["courriel"]:
                    ligne_dict["courriel"] = f"util_{ligne_dict.get('id')}@clinique.app"
                ligne_dict["mot_de_passe"] = ligne_dict.get("password") if ligne_dict.get("password") else "defaut123"
                ligne_dict["nom_utilisateur"] = ligne_dict.get("username")
                ligne_dict["telephone"] = ligne_dict.get("mobile")
                ligne_dict["est_actif"] = bool(ligne_dict.get("status", 1))
                ligne_dict["courriel_verifie_le"] = ligne_dict.get("email_verified_at")
                ligne_dict["code_otp"] = ligne_dict.get("otp")
                ligne_dict["secret_totp"] = ligne_dict.get("google2fa_secret")
                ligne_dict["totp_actif"] = bool(ligne_dict.get("is_google_authentication", 0))
                
            elif table_src == "appointment_transactions":
                ligne_dict["id_rendez_vous"] = ligne_dict.get("appointment_id")
                ligne_dict["montant"] = ligne_dict.get("total_amount") or 0.0
                ligne_dict["devise"] = "USD"
                ligne_dict["passerelle"] = ligne_dict.get("transaction_type", "system")
                ligne_dict["reference_transaction"] = ligne_dict.get("external_transaction_id", "N/A")
                ligne_dict["statut"] = "paid" if bool(ligne_dict.get("payment_status", 0)) else "pending"
                ligne_dict["reponse_passerelle"] = json.dumps({})

            elif table_src == "appointments":
                ligne_dict["reference"] = f"RDV-{ligne_dict.get('id', 0)}"
                ligne_dict["id_clinique"] = ligne_dict.get("clinic_id") or 1
                ligne_dict["id_medecin"] = ligne_dict.get("doctor_id") or 1
                ligne_dict["id_patient"] = ligne_dict.get("user_id") or 1
                ligne_dict["programme_le"] = ligne_dict.get("appointment_date")
                ligne_dict["duree_minutes"] = ligne_dict.get("duration") or 30
                ligne_dict["statut"] = ligne_dict.get("status") or "pending"
                ligne_dict["type"] = "in_person"
                
                montant_total = ligne_dict.get("total_amount") or 0.0
                montant_av = ligne_dict.get("advance_paid_amount") or 0.0
                ligne_dict["montant"] = montant_total
                ligne_dict["montant_avance"] = montant_av
                ligne_dict["statut_paiement"] = "paid" if montant_av >= montant_total else "pending"
                
                ligne_dict["passerelle_paiement"] = "system"
                ligne_dict["reference_paiement"] = "N/A"
                ligne_dict["notes"] = ligne_dict.get("appointment_extra_info")
                ligne_dict["motif_annulation"] = ligne_dict.get("reason")
                ligne_dict["id_evenement_google"] = ligne_dict.get("meet_link")
                ligne_dict["est_suivi"] = False
                ligne_dict["id_rdv_parent"] = None

            elif table_src == "billing_record":
                ligne_dict["id_rendez_vous"] = ligne_dict.get("encounter_id") or 1
                ligne_dict["id_patient"] = ligne_dict.get("user_id") or 1
                ligne_dict["sous_total"] = ligne_dict.get("service_amount") or 0.0
                ligne_dict["montant_remise"] = ligne_dict.get("discount_amount") or 0.0
                ligne_dict["montant_taxe"] = ligne_dict.get("final_tax_amount") or 0.0
                ligne_dict["total"] = ligne_dict.get("final_total_amount") or ligne_dict.get("total_amount") or 0.0
                ligne_dict["date_echeance"] = ligne_dict.get("date")
                ligne_dict["paye_le"] = ligne_dict.get("created_at") if ligne_dict.get("payment_status") == 1 else None
                ligne_dict["statut"] = "paid" if ligne_dict.get("payment_status") == 1 else "pending"

            elif table_src == "billing_item":
                ligne_dict["id_facture"] = ligne_dict.get("billing_id")
                ligne_dict["description"] = ligne_dict.get("item_name", "Service médical")
                ligne_dict["quantite"] = ligne_dict.get("quantity") or 1
                ligne_dict["prix_unitaire"] = ligne_dict.get("service_amount") or 0.0
                ligne_dict["sous_total"] = ligne_dict.get("total_amount") or 0.0
                ligne_dict["taux_taxe"] = 0.0

            elif table_src == "patient_encounters":
                ligne_dict["id_rendez_vous"] = ligne_dict.get("appointment_id") or 1
                ligne_dict["date_consultation"] = ligne_dict.get("encounter_date")
                ligne_dict["motif_principal"] = ligne_dict.get("description", "Consultation")
                ligne_dict["date_suivi"] = None
                ligne_dict["notes_suivi"] = None

            elif table_src == "encounter_medical_report":
                ligne_dict["id_consultation"] = ligne_dict.get("encounter_id") or 1
                ligne_dict["symptomes"] = "Symptômes généraux"
                ligne_dict["diagnostic"] = ligne_dict.get("name", "Examen clinique")
                ligne_dict["traitement"] = "Se référer aux ordonnances"
                ligne_dict["tension_arterielle"] = "120/80"
                ligne_dict["temperature"] = 37.0
                ligne_dict["poids"] = 70.0
                ligne_dict["notes_complementaires"] = f"Rapport médical daté du {ligne_dict.get('date')}"

            elif table_src == "encounter_prescription":
                ligne_dict["id_consultation"] = ligne_dict.get("encounter_id") or 1
                ligne_dict["nom_medicament"] = ligne_dict.get("name", "Médicament")
                ligne_dict["posologie"] = "1 comprimé"
                ligne_dict["frequence"] = ligne_dict.get("frequency", "1x par jour")
                duree_raw = ligne_dict.get("duration", "5")
                duree = 5
                if duree_raw:
                    chiffres = "".join(filter(str.isdigit, str(duree_raw)))
                    if chiffres:
                        duree = int(chiffres)
                ligne_dict["duree_jours"] = duree
                ligne_dict["instructions"] = ligne_dict.get("instruction")
                ligne_dict["est_chronique"] = False

            elif table_src == "vitals":
                ligne_dict["id_patient"] = ligne_dict.get("customer_id") or 1
                ligne_dict["taille"] = ligne_dict.get("height_cm") or 170.0
                ligne_dict["poids"] = ligne_dict.get("weight_kg") or 70.0
                ligne_dict["enregistre_le"] = ligne_dict.get("created_at")
                ligne_dict["enregistre_par"] = ligne_dict.get("created_by") or 1
                ligne_dict["tension_systolique"] = 120
                ligne_dict["tension_diastolique"] = 80
                ligne_dict["frequence_cardiaque"] = 72
                ligne_dict["temperature"] = 36.5
                ligne_dict["saturation_oxygene"] = 98
                ligne_dict["glycemie"] = 1.0
                ligne_dict["notes"] = "Signes vitaux initiaux"
                ligne_dict["id_rendez_vous"] = None

            elif table_src == "brands":
                ligne_dict["nom"] = ligne_dict.get("name")
                ligne_dict["identifiant_url"] = ligne_dict.get("slug")
                ligne_dict["est_actif"] = bool(ligne_dict.get("status", 1))

            elif table_src == "products":
                ligne_dict["id_prestataire"] = 1
                ligne_dict["nom"] = ligne_dict.get("name")
                ligne_dict["identifiant_url"] = ligne_dict.get("slug")
                ligne_dict["quantite_stock"] = ligne_dict.get("stock_qty", 0)
                ligne_dict["reference_article"] = ligne_dict.get("sku")
                ligne_dict["id_categorie"] = ligne_dict.get("category_id")
                ligne_dict["id_marque"] = ligne_dict.get("brand_id")
                ligne_dict["id_unite"] = ligne_dict.get("unit_id")
                ligne_dict["prix"] = ligne_dict.get("min_price", 0)
                ligne_dict["prix_remise"] = ligne_dict.get("discount_value")
                ligne_dict["est_actif"] = bool(ligne_dict.get("status", 1))
                ligne_dict["est_mis_en_avant"] = bool(ligne_dict.get("is_featured", 0))

            elif table_src == "settings":
                ligne_dict["cle"] = ligne_dict.get("name")
                ligne_dict["valeur"] = ligne_dict.get("val")
                type_src = ligne_dict.get("type", "string")
                if type_src == "string":
                    ligne_dict["type"] = "text"
                elif type_src == "array":
                    ligne_dict["type"] = "json"
                elif type_src in ("text", "number", "boolean", "json"):
                    ligne_dict["type"] = type_src
                else:
                    ligne_dict["type"] = "text"
                ligne_dict["est_public"] = True

            elif table_src == "sliders":
                ligne_dict["titre"] = ligne_dict.get("name")
                ligne_dict["est_actif"] = bool(ligne_dict.get("status", 1))

            elif table_src == "states":
                ligne_dict["nom"] = ligne_dict.get("name")
                ligne_dict["id_pays"] = ligne_dict.get("country_id")
                ligne_dict["code_region"] = f"REG-{ligne_dict.get('id', 0)}"

            elif table_src == "tags":
                ligne_dict["nom"] = ligne_dict.get("name")
                nom_tag = ligne_dict.get("name", "")
                slug = nom_tag.lower().replace(" ", "-").replace("/", "-")
                ligne_dict["identifiant_url"] = slug if slug else f"tag-{ligne_dict.get('id', 0)}"

            elif table_src == "taxes":
                ligne_dict["nom"] = ligne_dict.get("title")
                ligne_dict["tarif"] = ligne_dict.get("value", 0)
                ligne_dict["type"] = "percentage"
                ligne_dict["id_pays"] = 1
                ligne_dict["est_defaut"] = False
                ligne_dict["est_actif"] = bool(ligne_dict.get("status", 1))

            elif table_src == "units":
                ligne_dict["nom"] = ligne_dict.get("name")
                ligne_dict["abréviation"] = ligne_dict.get("slug", "un")
                ligne_dict["abreviation"] = ligne_dict.get("slug", "un")
                
            # Pour chaque colonne de la table cible
            for col_cible in colonnes_cible:
                valeur_trouvee = None
                
                # 1. Vérification dans le dictionnaire de correspondance
                source_colonne_nom = None
                for k_src, v_cible in CORRESPONDANCE_COLONNES.items():
                    if v_cible == col_cible:
                        source_colonne_nom = k_src
                        break
                
                # 2. Chercher dans ligne_dict
                if col_cible in ligne_dict:
                    valeur_trouvee = ligne_dict[col_cible]
                elif source_colonne_nom and source_colonne_nom in ligne_dict:
                    valeur_trouvee = ligne_dict[source_colonne_nom]
                
                # Traduire la valeur si c'est du texte cible
                if isinstance(valeur_trouvee, str):
                    valeur_trouvee = traduire_valeur(valeur_trouvee, col_cible, table_src)
                    
                valeurs_cible.append(valeur_trouvee)
                
            lignes_a_inserer.append(valeurs_cible)

        # Insérer les lignes dans la table cible
        placeholders = ", ".join(["%s"] * len(colonnes_cible))
        requete_insert = f"INSERT INTO clinique_dev.{table_cible} ({', '.join(colonnes_cible)}) VALUES ({placeholders})"

        try:
            await curseur_dev.executemany(requete_insert, lignes_a_inserer)
            print(f"  {len(lignes_a_inserer)} enregistrements insérés avec succès.")
        except Exception as e:
            print(f"  [ERREUR] Échec de l'insertion dans '{table_cible}' : {e}")

    # Réactiver les clés étrangères
    await curseur_dev.execute("SET FOREIGN_KEY_CHECKS = 1;")
    print("Vérification des clés étrangères réactivée.")

    await conn_en.ensure_closed()
    await conn_dev.ensure_closed()
    print("Migration et traduction terminées.")

if __name__ == "__main__":
    asyncio.run(main())
