"""
Scénario patient — browse + book.

Représente le flux complet d'un patient :
  1. Connexion
  2. Recherche de médecins / services
  3. Consultation des créneaux disponibles
  4. Réservation d'un RDV
  5. Consultation de son historique
"""
from locust import HttpUser, task, between, SequentialTaskSet
import random


PATIENT_EMAILS = [f"patient{i}@test.com" for i in range(1, 51)]
SPECIALTIES = ["cardiologie", "dermatologie", "pédiatrie", "médecine générale", "gynécologie"]


class PatientBrowseBook(SequentialTaskSet):
    """Séquence réaliste : recherche → slots → réservation → historique."""

    doctor_ids: list[int] = []
    appointment_id: int | None = None

    @task
    def step_search_doctors(self) -> None:
        """Étape 1 : recherche de médecins par spécialité."""
        specialty = random.choice(SPECIALTIES)
        resp = self.client.get(
            f"/api/doctors?search={specialty}&per_page=10",
            name="/api/doctors [search-specialty]",
        )
        if resp.status_code == 200:
            self.doctor_ids = [d["id"] for d in resp.json().get("items", [])]

    @task
    def step_view_slots(self) -> None:
        """Étape 2 : consultation des créneaux d'un médecin."""
        if not self.doctor_ids:
            return
        doctor_id = random.choice(self.doctor_ids)
        self.client.get(
            f"/api/doctors/{doctor_id}/slots?date=2026-07-20",
            name="/api/doctors/:id/slots [sequential]",
        )

    @task
    def step_view_history(self) -> None:
        """Étape 3 : consultation de l'historique de RDVs."""
        if not self.user.token:  # type: ignore[attr-defined]
            return
        self.client.get(
            "/api/appointments?page=1&status=completed",
            headers={"Authorization": f"Bearer {self.user.token}"},  # type: ignore[attr-defined]
            name="/api/appointments [history]",
        )


class ClinicPatientUser(HttpUser):
    """Utilisateur patient avec scénario browse + book."""

    tasks = [PatientBrowseBook]
    weight = 6
    wait_time = between(1, 4)
    token: str = ""

    def on_start(self) -> None:
        email = random.choice(PATIENT_EMAILS)
        resp = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": "test_password"},
            name="/api/auth/login [patient]",
        )
        if resp.status_code == 200:
            self.token = resp.json().get("access_token", "")
