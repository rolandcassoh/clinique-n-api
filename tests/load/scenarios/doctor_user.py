"""
Scénario médecin — view appointments.

Représente le flux d'un médecin en activité :
  1. Connexion
  2. Consultation du planning du jour
  3. Vérification des notifications / profil
"""
from locust import HttpUser, task, between
import random


DOCTOR_EMAILS = [f"doctor{i}@test.com" for i in range(1, 21)]


class DoctorViewAppointmentsUser(HttpUser):
    """Médecin consultant son planning et ses alertes."""

    weight = 2  # 20% du trafic global
    wait_time = between(2, 6)
    token: str = ""

    def on_start(self) -> None:
        """Connexion du médecin."""
        email = random.choice(DOCTOR_EMAILS)
        resp = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": "test_password"},
            name="/api/auth/login [doctor]",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")

    @property
    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    @task(10)
    def view_my_appointments(self) -> None:
        """Consultation du planning — action principale d'un médecin."""
        if not self.token:
            return
        self.client.get(
            "/api/doctor/appointments",
            headers=self.auth_headers,
            name="/api/doctor/appointments [planning]",
        )

    @task(4)
    def view_today_appointments(self) -> None:
        """Planning filtré sur la journée en cours."""
        if not self.token:
            return
        self.client.get(
            "/api/doctor/appointments?date=today",
            headers=self.auth_headers,
            name="/api/doctor/appointments [today]",
        )

    @task(3)
    def check_profile(self) -> None:
        """Vérification du profil et des notifications en attente."""
        if not self.token:
            return
        self.client.get(
            "/api/auth/me",
            headers=self.auth_headers,
            name="/api/auth/me [doctor]",
        )

    @task(1)
    def view_earnings(self) -> None:
        """Consultation des revenus / commissions."""
        if not self.token:
            return
        self.client.get(
            "/api/doctor/earnings",
            headers=self.auth_headers,
            name="/api/doctor/earnings",
        )
