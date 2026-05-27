from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import structlog

from app.config import settings

logger = structlog.get_logger()


@dataclass
class PushPayload:
    title: str
    body: str
    data: dict | None = None
    image_url: str | None = None
    click_action: str | None = None


class FirebaseAdapter:
    """
    Adaptateur Firebase Cloud Messaging (FCM).
    Supporte l'envoi individuel et multicast.
    Fallback gracieux si firebase-admin non configuré.
    """

    def __init__(self) -> None:
        self._app = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        if self._initialized:
            return self._app is not None
        self._initialized = True
        try:
            import firebase_admin
            from firebase_admin import credentials

            if not settings.firebase_credentials_path:
                logger.warning("firebase.credentials_not_configured")
                return False
            if not os.path.exists(settings.firebase_credentials_path):
                logger.warning(
                    "firebase.credentials_file_not_found",
                    path=settings.firebase_credentials_path,
                )
                return False
            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.firebase_credentials_path)
                self._app = firebase_admin.initialize_app(cred)
            else:
                self._app = firebase_admin.get_app()
            logger.info("firebase.initialized")
            return True
        except ImportError:
            logger.warning("firebase.firebase_admin_not_installed")
            return False
        except Exception as e:
            logger.error("firebase.init_failed", error=str(e))
            return False

    async def send_push(self, fcm_token: str, payload: PushPayload) -> bool:
        """Envoie une notification push à un token FCM."""
        if not self._ensure_initialized():
            logger.info("firebase.push_skipped_not_configured", title=payload.title)
            return False
        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(
                    title=payload.title,
                    body=payload.body,
                    image=payload.image_url,
                ),
                data={str(k): str(v) for k, v in (payload.data or {}).items()},
                token=fcm_token,
                android=messaging.AndroidConfig(priority="high"),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(aps=messaging.Aps(sound="default"))
                ),
            )
            response = messaging.send(message)
            logger.info("firebase.push_sent", message_id=response, title=payload.title)
            return True
        except Exception as e:
            logger.error("firebase.push_failed", error=str(e), title=payload.title)
            return False

    async def send_push_to_multiple(
        self, fcm_tokens: list[str], payload: PushPayload
    ) -> dict[str, int]:
        """Envoi multicast (max 500 tokens par batch FCM)."""
        if not fcm_tokens:
            return {"success": 0, "failure": 0}
        if not self._ensure_initialized():
            return {"success": 0, "failure": len(fcm_tokens)}
        try:
            from firebase_admin import messaging

            BATCH_SIZE = 500
            total_success = 0
            total_failure = 0
            for i in range(0, len(fcm_tokens), BATCH_SIZE):
                batch = fcm_tokens[i : i + BATCH_SIZE]
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(
                        title=payload.title, body=payload.body
                    ),
                    data={str(k): str(v) for k, v in (payload.data or {}).items()},
                    tokens=batch,
                )
                response = messaging.send_each_for_multicast(message)
                total_success += response.success_count
                total_failure += response.failure_count
            logger.info(
                "firebase.multicast_sent",
                success=total_success,
                failure=total_failure,
            )
            return {"success": total_success, "failure": total_failure}
        except Exception as e:
            logger.error("firebase.multicast_failed", error=str(e))
            return {"success": 0, "failure": len(fcm_tokens)}

    async def send_topic(self, topic: str, payload: PushPayload) -> bool:
        """Envoie à un topic FCM (ex: 'clinic_12_doctors')."""
        if not self._ensure_initialized():
            return False
        try:
            from firebase_admin import messaging

            message = messaging.Message(
                notification=messaging.Notification(
                    title=payload.title, body=payload.body
                ),
                data={str(k): str(v) for k, v in (payload.data or {}).items()},
                topic=topic,
            )
            messaging.send(message)
            return True
        except Exception as e:
            logger.error("firebase.topic_send_failed", topic=topic, error=str(e))
            return False
