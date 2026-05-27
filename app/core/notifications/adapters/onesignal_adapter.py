from __future__ import annotations

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


class OneSignalAdapter:
    """
    Adaptateur OneSignal REST API v1.
    Alternative/complément à Firebase pour les notifications push.
    """

    BASE_URL = "https://onesignal.com/api/v1"

    def __init__(self) -> None:
        self._app_id = settings.onesignal_app_id
        self._api_key = settings.onesignal_rest_api_key
        self._headers = {
            "Authorization": f"Basic {self._api_key}",
            "Content-Type": "application/json",
        }

    def _is_configured(self) -> bool:
        return bool(self._app_id and self._api_key)

    async def send_to_user(
        self,
        external_user_id: str,
        title: str,
        body: str,
        data: dict | None = None,
        url: str | None = None,
    ) -> bool:
        """Envoie une notification à un utilisateur via son external_id."""
        if not self._is_configured():
            logger.info("onesignal.skipped_not_configured", title=title)
            return False
        payload: dict = {
            "app_id": self._app_id,
            "include_external_user_ids": [external_user_id],
            "channel_for_external_user_ids": "push",
            "headings": {"en": title, "fr": title},
            "contents": {"en": body, "fr": body},
        }
        if data:
            payload["data"] = data
        if url:
            payload["url"] = url
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/notifications",
                    json=payload,
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                result = response.json()
                logger.info(
                    "onesignal.notification_sent",
                    recipients=result.get("recipients", 0),
                    title=title,
                )
                return True
        except Exception as e:
            logger.error("onesignal.send_failed", error=str(e), title=title)
            return False

    async def send_to_segment(
        self,
        segment: str,
        title: str,
        body: str,
        data: dict | None = None,
    ) -> bool:
        """Envoie à un segment OneSignal (ex: 'Doctors', 'Patients')."""
        if not self._is_configured():
            return False
        payload = {
            "app_id": self._app_id,
            "included_segments": [segment],
            "headings": {"en": title, "fr": title},
            "contents": {"en": body, "fr": body},
            "data": data or {},
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/notifications",
                    json=payload,
                    headers=self._headers,
                    timeout=15.0,
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(
                "onesignal.segment_send_failed", segment=segment, error=str(e)
            )
            return False

    async def cancel_notification(self, notification_id: str) -> bool:
        """Annule une notification planifiée."""
        if not self._is_configured():
            return False
        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/notifications/{notification_id}",
                    params={"app_id": self._app_id},
                    headers=self._headers,
                    timeout=15.0,
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(
                "onesignal.cancel_failed",
                notification_id=notification_id,
                error=str(e),
            )
            return False
