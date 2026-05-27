"""Service Google Calendar — synchronisation rendez-vous clinique."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import structlog

logger = structlog.get_logger()


@dataclass
class CalendarEvent:
    event_id: str
    title: str
    start: datetime
    end: datetime
    attendees: list[str]


class GoogleCalendarService:
    """
    Intégration Google Calendar API v3.
    Synchronise les rendez-vous clinique avec le calendrier Google du médecin.
    Les méthodes retournent None/False de façon gracieuse si la librairie
    google-api-python-client n'est pas installée ou si les tokens sont invalides.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, access_token: str, refresh_token: str) -> None:
        self._access_token = access_token
        self._refresh_token = refresh_token

    def _build_service(self):
        """Construit le client Google Calendar. Lazy init."""
        try:
            from google.oauth2.credentials import Credentials  # type: ignore
            from googleapiclient.discovery import build  # type: ignore
            from app.config import settings

            creds = Credentials(
                token=self._access_token,
                refresh_token=self._refresh_token,
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret,
                token_uri="https://oauth2.googleapis.com/token",
            )
            return build("calendar", "v3", credentials=creds, cache_discovery=False)
        except ImportError:
            logger.warning("google_calendar.library_missing",
                           detail="google-api-python-client not installed, Calendar disabled")
            return None
        except Exception as exc:
            logger.error("google_calendar.build_failed", error=str(exc))
            return None

    async def create_appointment_event(
        self,
        calendar_id: str,
        title: str,
        start: datetime,
        duration_minutes: int,
        doctor_email: str,
        patient_email: str,
        appointment_reference: str,
        notes: Optional[str] = None,
    ) -> Optional[str]:
        """
        Crée un événement Google Calendar.
        Retourne l'event_id ou None si Google API indisponible.
        """
        service = self._build_service()
        if not service:
            return None

        end = start + timedelta(minutes=duration_minutes)
        event = {
            "summary": title,
            "description": f"Référence : {appointment_reference}\n{notes or ''}".strip(),
            "start": {"dateTime": start.isoformat(), "timeZone": "Africa/Douala"},
            "end": {"dateTime": end.isoformat(), "timeZone": "Africa/Douala"},
            "attendees": [{"email": doctor_email}, {"email": patient_email}],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 30},
                ],
            },
        }

        try:
            created = (
                service.events()
                .insert(calendarId=calendar_id, body=event, sendNotifications=True)
                .execute()
            )
            event_id: str = created["id"]
            logger.info("google_calendar.event_created", event_id=event_id)
            return event_id
        except Exception as exc:
            logger.error("google_calendar.create_failed", error=str(exc))
            return None

    async def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Supprime un événement (annulation RDV). Notifie tous les participants."""
        service = self._build_service()
        if not service:
            return False
        try:
            service.events().delete(
                calendarId=calendar_id, eventId=event_id, sendUpdates="all"
            ).execute()
            logger.info("google_calendar.event_deleted", event_id=event_id)
            return True
        except Exception as exc:
            logger.error("google_calendar.delete_failed", event_id=event_id, error=str(exc))
            return False

    async def update_event(
        self,
        calendar_id: str,
        event_id: str,
        new_start: datetime,
        duration_minutes: int,
    ) -> bool:
        """Met à jour les horaires d'un événement (reprogrammation RDV)."""
        service = self._build_service()
        if not service:
            return False
        try:
            new_end = new_start + timedelta(minutes=duration_minutes)
            event = (
                service.events().get(calendarId=calendar_id, eventId=event_id).execute()
            )
            event["start"] = {"dateTime": new_start.isoformat(), "timeZone": "Africa/Douala"}
            event["end"] = {"dateTime": new_end.isoformat(), "timeZone": "Africa/Douala"}
            service.events().update(
                calendarId=calendar_id, eventId=event_id, body=event, sendUpdates="all"
            ).execute()
            logger.info("google_calendar.event_updated", event_id=event_id)
            return True
        except Exception as exc:
            logger.error("google_calendar.update_failed", event_id=event_id, error=str(exc))
            return False
