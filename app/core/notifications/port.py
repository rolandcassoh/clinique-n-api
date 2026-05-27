from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailMessage:
    to: str
    subject: str
    html_body: str
    text_body: str = ""


class NotificationPort(ABC):
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> None:
        """Send an email notification."""

    @abstractmethod
    async def send_sms(self, phone_number: str, text: str) -> None:
        """Send an SMS notification."""
