from __future__ import annotations

from pathlib import Path
from typing import Optional

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from app.config import settings

logger = structlog.get_logger()

# Répertoire des templates courriel
TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailService:
    """Service courriel SMTP avec templates Jinja2."""

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
        """Envoie un courriel HTML depuis un template Jinja2."""
        destinataires = [to] if isinstance(to, str) else to
        try:
            contenu_html = self._render(template_name, context)
        except Exception as erreur:
            logger.error(
                "courriel.rendu_template_echoue",
                template=template_name,
                error=str(erreur),
            )
            return False

        if not settings.smtp_host or settings.smtp_host == "localhost":
            # Mode développement : journalisation uniquement, pas d'envoi réel
            logger.info(
                "courriel.mode_dev_ignore",
                to=destinataires,
                subject=subject,
                template=template_name,
            )
            return True

        try:
            import aiosmtplib
            from courriel.mime.multipart import MIMEMultipart
            from courriel.mime.text import MIMEText

            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.smtp_from_email
            message["To"] = ", ".join(destinataires)
            if cc:
                message["Cc"] = ", ".join(cc)
            if reply_to:
                message["Reply-To"] = reply_to
            message.attach(MIMEText(contenu_html, "html", "utf-8"))

            utilisateur_smtp = settings.smtp_user or None
            mot_de_passe_smtp = settings.smtp_password or None

            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                nom_utilisateur=utilisateur_smtp,
                mot_de_passe=mot_de_passe_smtp,
                start_tls=settings.smtp_port == 587,
            )
            logger.info("courriel.envoye", to=destinataires, subject=subject)
            return True
        except ImportError:
            logger.warning("courriel.aiosmtplib_non_installe")
            return False
        except Exception as erreur:
            logger.error(
                "courriel.envoi_echoue", to=destinataires, subject=subject, error=str(erreur)
            )
            return False

    def _render(self, template_name: str, context: dict) -> str:
        gabarit = self._env.get_template(f"{template_name}.html")
        return gabarit.render(**context)


# Instance singleton du service courriel
email_service = EmailService()
