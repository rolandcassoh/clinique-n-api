"""Tests unitaires du système de notifications (Firebase, OneSignal, Email, Factory)."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# FirebaseAdapter
# ---------------------------------------------------------------------------

class TestFirebaseAdapter:
    """Tests de l'adaptateur Firebase Cloud Messaging."""

    @pytest.mark.asyncio
    async def test_send_push_without_credentials_returns_false(self):
        """Sans credentials configurés, send_push doit retourner False sans lever d'exception."""
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload

        adapter = FirebaseAdapter()
        # credentials_path vide par défaut dans les settings de test
        payload = PushPayload(title="Test", body="Corps du message")
        result = await adapter.send_push("fake_fcm_token", payload)
        assert result is False

    @pytest.mark.asyncio
    async def test_send_push_to_multiple_empty_tokens_returns_zero_counts(self):
        """Liste de tokens vide → {success: 0, failure: 0} sans appel Firebase."""
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload

        adapter = FirebaseAdapter()
        payload = PushPayload(title="Multicast", body="Corps")
        result = await adapter.send_push_to_multiple([], payload)
        assert result == {"success": 0, "failure": 0}

    @pytest.mark.asyncio
    async def test_send_push_to_multiple_not_initialized_returns_failure_count(self):
        """Sans credentials, tous les tokens sont comptés en failure."""
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload

        adapter = FirebaseAdapter()
        payload = PushPayload(title="Multicast", body="Corps")
        tokens = ["token1", "token2", "token3"]
        result = await adapter.send_push_to_multiple(tokens, payload)
        assert result["success"] == 0
        assert result["failure"] == 3

    @pytest.mark.asyncio
    async def test_send_push_firebase_admin_not_installed_returns_false(self):
        """Si firebase_admin n'est pas installé, send_push doit retourner False gracieusement."""
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload

        adapter = FirebaseAdapter()

        # Simuler un chemin de credentials défini mais firebase_admin manquant
        with patch("app.core.notifications.adapters.firebase_adapter.settings") as mock_settings:
            mock_settings.firebase_credentials_path = "/fake/credentials.json"
            with patch("builtins.__import__", side_effect=ImportError("No module named 'firebase_admin'")):
                # Reset l'état initialized pour forcer la ré-initialisation
                adapter._initialized = False
                adapter._app = None
                payload = PushPayload(title="Test", body="Corps")
                result = await adapter.send_push("token123", payload)
                assert result is False

    @pytest.mark.asyncio
    async def test_send_topic_without_credentials_returns_false(self):
        """send_topic sans credentials retourne False."""
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload

        adapter = FirebaseAdapter()
        payload = PushPayload(title="Topic Test", body="Corps")
        result = await adapter.send_topic("clinic_12_doctors", payload)
        assert result is False

    def test_push_payload_defaults(self):
        """PushPayload a des valeurs par défaut correctes."""
        from app.core.notifications.adapters.firebase_adapter import PushPayload

        p = PushPayload(title="Titre", body="Corps")
        assert p.data is None
        assert p.image_url is None
        assert p.click_action is None


# ---------------------------------------------------------------------------
# OneSignalAdapter
# ---------------------------------------------------------------------------

class TestOneSignalAdapter:
    """Tests de l'adaptateur OneSignal."""

    @pytest.mark.asyncio
    async def test_send_to_user_not_configured_returns_false(self):
        """Sans app_id et api_key, send_to_user doit retourner False."""
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        with patch("app.core.notifications.adapters.onesignal_adapter.settings") as mock_settings:
            mock_settings.onesignal_app_id = ""
            mock_settings.onesignal_rest_api_key = ""
            adapter = OneSignalAdapter()
            result = await adapter.send_to_user("user_123", "Titre", "Corps")
            assert result is False

    @pytest.mark.asyncio
    async def test_send_to_segment_not_configured_returns_false(self):
        """Sans configuration, send_to_segment retourne False."""
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        with patch("app.core.notifications.adapters.onesignal_adapter.settings") as mock_settings:
            mock_settings.onesignal_app_id = ""
            mock_settings.onesignal_rest_api_key = ""
            adapter = OneSignalAdapter()
            result = await adapter.send_to_segment("Doctors", "Titre", "Corps")
            assert result is False

    @pytest.mark.asyncio
    async def test_cancel_notification_not_configured_returns_false(self):
        """Sans configuration, cancel_notification retourne False."""
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        with patch("app.core.notifications.adapters.onesignal_adapter.settings") as mock_settings:
            mock_settings.onesignal_app_id = ""
            mock_settings.onesignal_rest_api_key = ""
            adapter = OneSignalAdapter()
            result = await adapter.cancel_notification("notif-id-123")
            assert result is False

    def test_is_configured_returns_true_when_credentials_set(self):
        """_is_configured retourne True quand app_id et api_key sont définis."""
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        with patch("app.core.notifications.adapters.onesignal_adapter.settings") as mock_settings:
            mock_settings.onesignal_app_id = "app-id-xyz"
            mock_settings.onesignal_rest_api_key = "rest-key-xyz"
            adapter = OneSignalAdapter()
            assert adapter._is_configured() is True

    @pytest.mark.asyncio
    async def test_send_to_user_http_error_returns_false(self):
        """Une erreur HTTP lors de l'envoi retourne False sans exception."""
        import httpx
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        with patch("app.core.notifications.adapters.onesignal_adapter.settings") as mock_settings:
            mock_settings.onesignal_app_id = "app-id"
            mock_settings.onesignal_rest_api_key = "api-key"
            adapter = OneSignalAdapter()

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))

                result = await adapter.send_to_user("user_1", "Titre", "Corps")
                assert result is False


# ---------------------------------------------------------------------------
# EmailService
# ---------------------------------------------------------------------------

class TestEmailService:
    """Tests du service email SMTP avec Jinja2."""

    @pytest.mark.asyncio
    async def test_send_dev_mode_returns_true(self):
        """En mode dev (smtp_host=localhost), send() retourne True sans envoyer."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        # smtp_host par défaut est "localhost" dans la config de dev
        result = await svc.send(
            to="patient@example.com",
            subject="Test email",
            template_name="appointment_confirmation",
            context={
                "patient_name": "Jean Dupont",
                "reference": "REF-001",
                "doctor_name": "Martin",
                "clinic_name": "Clinique Test",
                "scheduled_at": "2026-06-01 09:00",
                "amount": "15000",
                "app_name": "Gestion Clinique",
            },
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_unknown_template_returns_false(self):
        """Un template inexistant retourne False sans lever d'exception."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        result = await svc.send(
            to="user@example.com",
            subject="Test",
            template_name="template_inexistant",
            context={},
        )
        assert result is False

    def test_render_raises_on_unknown_template(self):
        """_render() lève une exception si le template n'existe pas."""
        from app.core.notifications.email_service import EmailService
        from jinja2 import TemplateNotFound

        svc = EmailService()
        with pytest.raises(Exception):
            svc._render("template_qui_nexiste_pas", {})

    def test_render_appointment_confirmation(self):
        """_render() génère du HTML pour appointment_confirmation."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        html = svc._render("appointment_confirmation", {
            "patient_name": "Marie Curie",
            "reference": "REF-2026-001",
            "doctor_name": "Dupont",
            "clinic_name": "Clinique Nord",
            "scheduled_at": "01/06/2026 à 10h00",
            "amount": "20000",
            "app_name": "Clinique App",
        })
        assert "Marie Curie" in html
        assert "REF-2026-001" in html
        assert "Dupont" in html

    def test_render_otp_verification(self):
        """_render() génère du HTML avec le code OTP."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        html = svc._render("otp_verification", {
            "user_name": "Pierre Martin",
            "otp_code": "847291",
            "expires_in": "10 minutes",
        })
        assert "847291" in html
        assert "Pierre Martin" in html

    def test_render_password_reset(self):
        """_render() génère du HTML avec le lien de reset."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        html = svc._render("password_reset", {
            "user_name": "Alice",
            "reset_url": "https://app.clinique.cm/reset?token=abc123",
            "expires_in": "30 minutes",
        })
        assert "https://app.clinique.cm/reset?token=abc123" in html

    @pytest.mark.asyncio
    async def test_send_list_of_recipients_dev_mode(self):
        """send() accepte une liste de destinataires."""
        from app.core.notifications.email_service import EmailService

        svc = EmailService()
        result = await svc.send(
            to=["a@example.com", "b@example.com"],
            subject="Multi-destinataires",
            template_name="appointment_reminder",
            context={
                "patient_name": "Paul",
                "doctor_name": "Bernard",
                "scheduled_at": "02/06/2026",
                "clinic_name": "Clinique Sud",
                "reference": "REF-002",
            },
        )
        assert result is True


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestNotificationFactory:
    """Tests de la factory de notifications."""

    def test_get_firebase_returns_firebase_adapter(self):
        from app.core.notifications.factory import get_firebase
        from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter

        adapter = get_firebase()
        assert isinstance(adapter, FirebaseAdapter)

    def test_get_onesignal_returns_onesignal_adapter(self):
        from app.core.notifications.factory import get_onesignal
        from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter

        adapter = get_onesignal()
        assert isinstance(adapter, OneSignalAdapter)

    def test_get_email_service_returns_email_service(self):
        from app.core.notifications.factory import get_email_service
        from app.core.notifications.email_service import EmailService

        svc = get_email_service()
        assert isinstance(svc, EmailService)

    @pytest.mark.asyncio
    async def test_notify_appointment_confirmed_no_token_sends_email_only(self):
        """Quand patient_fcm_token=None, seul l'email est envoyé, pas d'erreur."""
        from app.core.notifications import factory

        email_mock = AsyncMock(return_value=True)
        with patch.object(factory._email_service, "send", email_mock):
            await factory.notify_appointment_confirmed(
                patient_fcm_token=None,
                patient_email="patient@example.com",
                context={
                    "patient_name": "Jean",
                    "reference": "REF-001",
                    "doctor_name": "Smith",
                    "clinic_name": "Clinique Test",
                    "scheduled_at": "2026-06-01 09:00",
                    "amount": "15000",
                    "app_name": "App",
                },
            )
        # L'email doit avoir été envoyé une fois
        email_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_appointment_confirmed_with_token_calls_push_and_email(self):
        """Quand un token FCM est fourni, push + email sont appelés."""
        from app.core.notifications import factory

        email_mock = AsyncMock(return_value=True)
        push_mock = AsyncMock(return_value=True)

        with patch.object(factory._email_service, "send", email_mock):
            with patch.object(factory._firebase, "send_push", push_mock):
                await factory.notify_appointment_confirmed(
                    patient_fcm_token="fcm_token_abc",
                    patient_email="patient@example.com",
                    context={
                        "patient_name": "Jean",
                        "reference": "REF-001",
                        "doctor_name": "Smith",
                        "clinic_name": "Clinique Test",
                        "scheduled_at": "2026-06-01 09:00",
                        "amount": "15000",
                        "app_name": "App",
                    },
                )
        push_mock.assert_called_once()
        email_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_notify_appointment_cancelled_no_token(self):
        """notify_appointment_cancelled sans token ne lève pas d'exception."""
        from app.core.notifications import factory

        email_mock = AsyncMock(return_value=True)
        with patch.object(factory._email_service, "send", email_mock):
            await factory.notify_appointment_cancelled(
                patient_fcm_token=None,
                patient_email="patient@example.com",
                context={
                    "patient_name": "Jean",
                    "reference": "REF-001",
                    "scheduled_at": "2026-06-01 09:00",
                },
            )
        email_mock.assert_called_once()
