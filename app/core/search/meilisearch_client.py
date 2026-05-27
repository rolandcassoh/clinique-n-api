"""Client Meilisearch — connexion et health check."""
from __future__ import annotations

from typing import Optional

import structlog

logger = structlog.get_logger()


def get_meilisearch_client():
    """
    Retourne un client Meilisearch configuré ou None si non disponible.
    Effectue un health check pour valider la connexion.
    """
    try:
        import meilisearch  # type: ignore
        from app.config import settings

        client = meilisearch.Client(settings.meilisearch_url, settings.meilisearch_master_key)
        client.health()  # Lève une exception si Meilisearch est inaccessible
        return client
    except ImportError:
        logger.warning("meilisearch.library_missing", detail="meilisearch Python client not installed")
        return None
    except Exception as exc:
        logger.warning("meilisearch.unavailable", error=str(exc))
        return None
