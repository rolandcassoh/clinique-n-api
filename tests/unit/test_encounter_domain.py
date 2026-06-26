"""Tests unitaires du domaine encounter."""
from __future__ import annotations

import pytest

from app.modules.consultation.domain.entites import (
    BodyChart,
    EncounterStatus,
    MedicalReport,
    PatientEncounter,
    Prescription,
)
from app.modules.consultation.domain.exceptions import UnauthorizedMedicalAccessError
from app.core.crypto.field_encryption import FieldEncryption


# ---------------------------------------------------------------------------
# Chiffrement
# ---------------------------------------------------------------------------

class TestFieldEncryption:
    def test_encrypt_returns_different_value(self):
        plaintext = "Hypertension artérielle"
        encrypted = FieldEncryption.encrypt(plaintext)
        assert encrypted != plaintext
        assert len(encrypted) > 0

    def test_decrypt_roundtrip(self):
        plaintext = "Diabète de type 2"
        encrypted = FieldEncryption.encrypt(plaintext)
        decrypted = FieldEncryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string_returns_empty(self):
        assert FieldEncryption.encrypt("") == ""

    def test_decrypt_empty_string_returns_empty(self):
        assert FieldEncryption.decrypt("") == ""

    def test_decrypt_unencrypted_fallback(self):
        """Si la valeur n'est pas chiffrée (migration), retourne la valeur telle quelle."""
        plaintext = "not encrypted"
        result = FieldEncryption.decrypt(plaintext)
        assert result == plaintext

    def test_multiple_encryptions_differ(self):
        """Fernet utilise un nonce aléatoire, donc deux chiffrements du même texte diffèrent."""
        plaintext = "hypertension"
        enc1 = FieldEncryption.encrypt(plaintext)
        enc2 = FieldEncryption.encrypt(plaintext)
        assert enc1 != enc2
        assert FieldEncryption.decrypt(enc1) == plaintext
        assert FieldEncryption.decrypt(enc2) == plaintext


# ---------------------------------------------------------------------------
# MedicalReport
# ---------------------------------------------------------------------------

class TestMedicalReport:
    def test_medical_report_creation(self):
        report = MedicalReport(
            id=1,
            encounter_id=10,
            symptoms="Fièvre, toux",
            diagnosis="Grippe saisonnière",
            treatment="Paracétamol 1g x3/j",
        )
        assert report.id == 1
        assert report.encounter_id == 10
        assert report.symptoms == "Fièvre, toux"
        assert report.diagnosis == "Grippe saisonnière"
        assert report.treatment == "Paracétamol 1g x3/j"

    def test_medical_report_optional_fields_none(self):
        report = MedicalReport(id=1, encounter_id=1)
        assert report.symptoms is None
        assert report.diagnosis is None
        assert report.treatment is None
        assert report.blood_pressure is None


# ---------------------------------------------------------------------------
# Prescription
# ---------------------------------------------------------------------------

class TestPrescription:
    def test_prescription_creation(self):
        presc = Prescription(
            id=1,
            encounter_id=5,
            medication_name="Amoxicilline",
            dosage="500mg",
            frequency="3 fois par jour",
            duration_days=7,
            is_chronic=False,
        )
        assert presc.medication_name == "Amoxicilline"
        assert presc.is_chronic is False
        assert presc.duration_days == 7

    def test_chronic_prescription(self):
        presc = Prescription(
            id=2,
            encounter_id=5,
            medication_name="Metformine",
            dosage="850mg",
            frequency="2 fois par jour",
            is_chronic=True,
        )
        assert presc.is_chronic is True
        assert presc.duration_days is None


# ---------------------------------------------------------------------------
# PatientEncounter
# ---------------------------------------------------------------------------

class TestPatientEncounter:
    def test_encounter_default_status_is_open(self):
        enc = PatientEncounter(
            id=1,
            doctor_id=10,
            patient_id=20,
            status=EncounterStatus.OPEN,
        )
        assert enc.status == EncounterStatus.OPEN

    def test_encounter_close(self):
        enc = PatientEncounter(
            id=1, doctor_id=10, patient_id=20, status=EncounterStatus.OPEN
        )
        enc.close()
        assert enc.status == EncounterStatus.CLOSED

    def test_encounter_reopen(self):
        enc = PatientEncounter(
            id=1, doctor_id=10, patient_id=20, status=EncounterStatus.CLOSED
        )
        enc.reopen()
        assert enc.status == EncounterStatus.OPEN

    def test_patient_cannot_access_medical_report_data(self):
        """Le patient ne doit pas voir les données chiffrées — simulé via contrôle domaine."""
        enc = PatientEncounter(
            id=1, doctor_id=10, patient_id=20, status=EncounterStatus.OPEN,
            chief_complaint="Mal de tête",
        )
        # Le patient peut lire chief_complaint
        assert enc.chief_complaint == "Mal de tête"
        # Les données médicales (symptoms, diagnosis, treatment) vivent dans MedicalReport
        # et ne sont accessibles qu'au médecin — aucun attribut sur PatientEncounter
        assert not hasattr(enc, "symptoms")
        assert not hasattr(enc, "diagnosis")


# ---------------------------------------------------------------------------
# BodyChart
# ---------------------------------------------------------------------------

class TestBodyChart:
    def test_bodychart_creation(self):
        chart = BodyChart(
            id=1,
            appointment_id=5,
            image_url="https://example.com/body.png",
            annotations=[{"x": 10.0, "y": 20.0, "label": "douleur", "color": "#FF0000"}],
            notes="Zone inflammatoire épaule gauche",
        )
        assert chart.appointment_id == 5
        assert len(chart.annotations) == 1
        assert chart.annotations[0]["label"] == "douleur"
