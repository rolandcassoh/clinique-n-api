from __future__ import annotations

from app.core.notifications.adapters.firebase_adapter import FirebaseAdapter, PushPayload
from app.core.notifications.adapters.onesignal_adapter import OneSignalAdapter
from app.core.notifications.email_service import email_service as _email_service

# Singletons
_firebase = FirebaseAdapter()
_onesignal = OneSignalAdapter()


def get_firebase() -> FirebaseAdapter:
    return _firebase


def get_onesignal() -> OneSignalAdapter:
    return _onesignal


def get_email_service():
    """Retourne le singleton EmailService."""
    return _email_service


async def notify_appointment_confirmed(
    patient_fcm_token: str | None,
    patient_email: str,
    context: dict,
) -> None:
    """Notification multi-canal : push Firebase + email."""
    if patient_fcm_token:
        await _firebase.send_push(
            patient_fcm_token,
            PushPayload(
                title="Rendez-vous confirmé ✅",
                body=f"Votre RDV du {context.get('scheduled_at', '')} est confirmé",
                data={
                    "type": "appointment_confirmed",
                    "reference": context.get("reference", ""),
                },
            ),
        )
    await _email_service.send(
        to=patient_email,
        subject=f"Confirmation de votre rendez-vous {context.get('reference', '')}",
        template_name="appointment_confirmation",
        context=context,
    )


async def notify_appointment_cancelled(
    patient_fcm_token: str | None,
    patient_email: str,
    context: dict,
) -> None:
    """Notification multi-canal : push Firebase + email (annulation)."""
    if patient_fcm_token:
        await _firebase.send_push(
            patient_fcm_token,
            PushPayload(
                title="Rendez-vous annulé ❌",
                body=f"Votre RDV {context.get('reference', '')} a été annulé",
                data={"type": "appointment_cancelled"},
            ),
        )
    await _email_service.send(
        to=patient_email,
        subject=f"Annulation de votre rendez-vous {context.get('reference', '')}",
        template_name="appointment_cancellation",
        context=context,
    )


async def notify_appointment_reminder(
    patient_fcm_token: str | None,
    patient_email: str,
    context: dict,
) -> None:
    """Rappel de rendez-vous J-1."""
    if patient_fcm_token:
        await _firebase.send_push(
            patient_fcm_token,
            PushPayload(
                title="Rappel rendez-vous ⏰",
                body=f"Votre RDV est demain : {context.get('scheduled_at', '')}",
                data={
                    "type": "appointment_reminder",
                    "reference": context.get("reference", ""),
                },
            ),
        )
    await _email_service.send(
        to=patient_email,
        subject=f"Rappel : votre rendez-vous {context.get('reference', '')} est demain",
        template_name="appointment_reminder",
        context=context,
    )


async def notify_password_reset(user_email: str, context: dict) -> None:
    """Email de réinitialisation de mot de passe."""
    await _email_service.send(
        to=user_email,
        subject="Réinitialisation de votre mot de passe",
        template_name="password_reset",
        context=context,
    )


async def notify_otp(user_email: str, context: dict) -> None:
    """Email de code OTP."""
    await _email_service.send(
        to=user_email,
        subject=f"Votre code de vérification : {context.get('otp_code', '')}",
        template_name="otp_verification",
        context=context,
    )
