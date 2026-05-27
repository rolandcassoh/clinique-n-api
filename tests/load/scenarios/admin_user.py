"""
Scénario administrateur — dashboard.

Représente le flux d'un admin clinique :
  1. Connexion
  2. Tableau de bord (RDVs, facturation)
  3. Gestion des médecins / utilisateurs
  4. Consultation des rapports
"""
from locust import HttpUser, task, between


class AdminDashboardUser(HttpUser):
    """Administrateur clinique gérant le back-office."""

    weight = 2  # 20% du trafic global
    wait_time = between(3, 8)
    token: str = ""

    def on_start(self) -> None:
        """Connexion administrateur."""
        resp = self.client.post(
            "/api/auth/login",
            json={"email": "admin@test.com", "password": "test_password"},
            name="/api/auth/login [admin]",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(8)
    def dashboard_appointments(self) -> None:
        """Vue globale des RDVs — tableau de bord principal."""
        if not self.token:
            return
        self.client.get(
            "/api/admin/appointments?page=1&per_page=20",
            headers=self.auth_headers,
            name="/api/admin/appointments [dashboard]",
        )

    @task(4)
    def admin_billing(self) -> None:
        """Consultation de la facturation et des revenus globaux."""
        if not self.token:
            return
        self.client.get(
            "/api/admin/billing?page=1",
            headers=self.auth_headers,
            name="/api/admin/billing",
        )

    @task(3)
    def admin_doctors_list(self) -> None:
        """Gestion de la liste des médecins."""
        if not self.token:
            return
        self.client.get(
            "/api/doctors?page=1&per_page=20",
            headers=self.auth_headers,
            name="/api/admin/doctors [list]",
        )

    @task(2)
    def admin_subscriptions(self) -> None:
        """Suivi des abonnements actifs."""
        if not self.token:
            return
        self.client.get(
            "/api/admin/subscriptions?status=active&page=1",
            headers=self.auth_headers,
            name="/api/admin/subscriptions",
        )

    @task(1)
    def admin_commissions(self) -> None:
        """Rapport des commissions."""
        if not self.token:
            return
        self.client.get(
            "/api/commissions?page=1",
            headers=self.auth_headers,
            name="/api/admin/commissions",
        )
