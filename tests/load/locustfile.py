"""
Tests de charge Locust — Gestion Clinique API

Utilisateurs simulés :
  - PatientUser  (60%) : consultation de médecins, réservation de RDVs, panier
  - DoctorUser   (20%) : consultation du planning, notifications
  - AdminUser    (20%) : tableau de bord, facturation, gestion médecins

Usage :
  locust --headless --users 200 --spawn-rate 10 \\
         --host https://staging-api.clinique.app \\
         --run-time 5m \\
         --csv results/load_test_$(date +%Y%m%d_%H%M)
"""
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner
import random
import json


class PatientUser(HttpUser):
    """Simule un patient qui consulte et réserve des RDVs."""

    weight = 6  # 60% du trafic
    wait_time = between(1, 4)
    token: str = ""
    doctor_ids: list[int] = []

    def on_start(self) -> None:
        """Connexion et récupération du catalogue médecins au démarrage."""
        resp = self.client.post(
            "/api/auth/login",
            json={
                "email": f"patient{random.randint(1, 50)}@test.com",
                "password": "test_password",
            },
            name="/api/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

        # Récupérer les IDs de médecins pour les scénarios de slots
        resp = self.client.get("/api/doctors?per_page=20", name="/api/doctors [list]")
        if resp.status_code == 200:
            self.doctor_ids = [d["id"] for d in resp.json().get("items", [])]

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(15)
    def browse_doctors(self) -> None:
        """Navigation dans la liste des médecins — tâche la plus fréquente."""
        self.client.get(
            "/api/doctors?page=1&per_page=10",
            name="/api/doctors [browse]",
        )

    @task(10)
    def get_doctor_slots(self) -> None:
        """Consultation des créneaux disponibles d'un médecin."""
        if not self.doctor_ids:
            return
        doctor_id = random.choice(self.doctor_ids)
        self.client.get(
            f"/api/doctors/{doctor_id}/slots?date=2026-07-15",
            name="/api/doctors/:id/slots",
        )

    @task(8)
    def browse_products(self) -> None:
        """Navigation dans la boutique de produits."""
        self.client.get(
            "/api/products?page=1&per_page=12",
            name="/api/products [browse]",
        )

    @task(6)
    def browse_services(self) -> None:
        """Navigation dans le catalogue de services."""
        self.client.get("/api/services?page=1", name="/api/services [browse]")

    @task(4)
    def list_my_appointments(self) -> None:
        """Consultation des RDVs du patient connecté."""
        if not self.token:
            return
        self.client.get(
            "/api/appointments?page=1",
            headers=self.auth_headers,
            name="/api/appointments [mine]",
        )

    @task(3)
    def view_cart(self) -> None:
        """Consultation du panier."""
        if not self.token:
            return
        self.client.get(
            "/api/cart",
            headers=self.auth_headers,
            name="/api/cart [view]",
        )

    @task(2)
    def search_doctors(self) -> None:
        """Recherche textuelle de médecins par spécialité."""
        terms = ["cardio", "généraliste", "pédiatre", "dermato"]
        self.client.get(
            f"/api/doctors?search={random.choice(terms)}",
            name="/api/doctors [search]",
        )

    @task(1)
    def check_wallet(self) -> None:
        """Consultation du portefeuille électronique."""
        if not self.token:
            return
        self.client.get(
            "/api/wallet",
            headers=self.auth_headers,
            name="/api/wallet",
        )


class DoctorUser(HttpUser):
    """Simule un médecin qui consulte son planning et ses notifications."""

    weight = 2  # 20% du trafic
    wait_time = between(2, 6)
    token: str = ""

    def on_start(self) -> None:
        """Connexion au démarrage."""
        resp = self.client.post(
            "/api/auth/login",
            json={
                "email": f"doctor{random.randint(1, 20)}@test.com",
                "password": "test_password",
            },
            name="/api/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def view_appointments(self) -> None:
        """Consultation du planning du médecin — tâche principale."""
        if not self.token:
            return
        self.client.get(
            "/api/doctor/appointments",
            headers=self.auth_headers,
            name="/api/doctor/appointments",
        )

    @task(3)
    def check_notifications(self) -> None:
        """Vérification du profil et des notifications."""
        if not self.token:
            return
        self.client.get(
            "/api/auth/me",
            headers=self.auth_headers,
            name="/api/auth/me",
        )


class AdminUser(HttpUser):
    """Simule un administrateur clinique gérant le tableau de bord."""

    weight = 2  # 20% du trafic
    wait_time = between(3, 8)
    token: str = ""

    def on_start(self) -> None:
        """Connexion admin au démarrage."""
        resp = self.client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "test_password"},
            name="/api/auth/login",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(8)
    def dashboard_appointments(self) -> None:
        """Vue admin de tous les RDVs — tableau de bord principal."""
        if not self.token:
            return
        self.client.get(
            "/api/admin/appointments?page=1&per_page=20",
            headers=self.auth_headers,
            name="/api/admin/appointments",
        )

    @task(4)
    def admin_billing(self) -> None:
        """Consultation de la facturation globale."""
        if not self.token:
            return
        self.client.get(
            "/api/admin/billing?page=1",
            headers=self.auth_headers,
            name="/api/admin/billing",
        )

    @task(2)
    def admin_doctors(self) -> None:
        """Liste des médecins depuis la vue admin."""
        if not self.token:
            return
        self.client.get(
            "/api/doctors?page=1&per_page=20",
            headers=self.auth_headers,
            name="/api/admin/doctors",
        )
