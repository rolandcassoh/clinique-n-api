from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from app.config import settings

logger = structlog.get_logger()

# Répertoire des templates email
TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailService:
    """Service email SMTP avec templates Jinja2."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(["html"]),
        )

    async def send(
        self,
        to: str | list[str],
        subject: str,
        template_name: str,
        context: dict,
        cc: list[str] | None = None,
        reply_to: str | None = None,
    ) -> bool:
        """Envoie un email HTML depuis un template Jinja2."""
        recipients = [to] if isinstance(to, str) else to
        try:
            html_content = self._render(template_name, context)
        except Exception as e:
            logger.error(
                "email.template_render_failed",
                template=template_name,
                error=str(e),
            )
            return False

        if not settings.smtp_host or settings.smtp_host == "localhost":
            # Mode développement : logger seulement
            logger.info(
                "email.dev_mode_skipped",
                to=recipients,
                subject=subject,
                template=template_name,
            )
            return True

        try:
            import aiosmtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.smtp_from_email
            msg["To"] = ", ".join(recipients)
            if cc:
                msg["Cc"] = ", ".join(cc)
            if reply_to:
                msg["Reply-To"] = reply_to
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            smtp_user = settings.smtp_user or None
            smtp_password = settings.smtp_password or None

            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=smtp_user,
                password=smtp_password,
                start_tls=settings.smtp_port == 587,
            )
            logger.info("email.sent", to=recipients, subject=subject)
            return True
        except ImportError:
            logger.warning("email.aiosmtplib_not_installed")
            return False
        except Exception as e:
            logger.error(
                "email.send_failed", to=recipients, subject=subject, error=str(e)
            )
            return False

    def _render(self, template_name: str, context: dict) -> str:
        template = self._env.get_template(f"{template_name}.html")
        return template.render(**context)


# Instance singleton
email_service = EmailService()
