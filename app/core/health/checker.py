from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog

from app.config import settings

logger = structlog.get_logger()


@dataclass
class ServiceHealth:
    nom: str
    statut: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: float
    details: dict = field(default_factory=dict)


@dataclass
class HealthReport:
    statut: str
    timestamp: str
    version: str
    services: list[ServiceHealth] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.statut == "healthy"

    def to_dict(self) -> dict:
        return {
            "statut": self.statut,
            "timestamp": self.timestamp,
            "version": self.version,
            "services": [
                {
                    "nom": s.nom,
                    "statut": s.statut,
                    "latency_ms": s.latency_ms,
                    "details": s.details,
                }
                for s in self.services
            ],
        }


async def check_database() -> ServiceHealth:
    """Vérifie la connectivité à la base de données."""
    debut = time.monotonic()
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        latence = (time.monotonic() - debut) * 1000
        return ServiceHealth("database", "healthy", round(latence, 2))
    except Exception as erreur:
        latence = (time.monotonic() - debut) * 1000
        logger.warning("sante.base_de_donnees_indisponible", error=str(erreur))
        return ServiceHealth(
            "database", "unhealthy", round(latence, 2), {"error": str(erreur)}
        )


async def check_redis() -> ServiceHealth:
    """Vérifie la connectivité à Redis."""
    debut = time.monotonic()
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        latence = (time.monotonic() - debut) * 1000
        return ServiceHealth("redis", "healthy", round(latence, 2))
    except Exception as erreur:
        latence = (time.monotonic() - debut) * 1000
        logger.warning("sante.redis_degrade", error=str(erreur))
        return ServiceHealth(
            "redis", "degraded", round(latence, 2), {"error": str(erreur)}
        )


async def check_meilisearch() -> ServiceHealth:
    """Vérifie la connectivité à Meilisearch."""
    debut = time.monotonic()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            reponse = await client.get(f"{settings.meilisearch_url}/health")
        latence = (time.monotonic() - debut) * 1000
        if reponse.status_code == 200:
            return ServiceHealth("meilisearch", "healthy", round(latence, 2))
        return ServiceHealth(
            "meilisearch",
            "degraded",
            round(latence, 2),
            {"status_code": reponse.status_code},
        )
    except Exception as erreur:
        latence = (time.monotonic() - debut) * 1000
        logger.warning("sante.meilisearch_degrade", error=str(erreur))
        return ServiceHealth(
            "meilisearch", "degraded", round(latence, 2), {"error": str(erreur)}
        )


async def get_health_report() -> HealthReport:
    """Effectue tous les health checks en parallèle et retourne le rapport global."""
    verifications = await asyncio.gather(
        check_database(),
        check_redis(),
        check_meilisearch(),
        return_exceptions=True,
    )

    services: list[ServiceHealth] = []
    for verification in verifications:
        if isinstance(verification, Exception):
            services.append(
                ServiceHealth("unknown", "unhealthy", 0.0, {"error": str(verification)})
            )
        else:
            services.append(verification)

    # Statut global : unhealthy si la BDD est down, degraded si d'autres services sont dégradés
    sante_bdd = next((s for s in services if s.nom == "database"), None)
    if sante_bdd and sante_bdd.statut == "unhealthy":
        statut_global = "unhealthy"
    elif any(s.statut != "healthy" for s in services):
        statut_global = "degraded"
    else:
        statut_global = "healthy"

    return HealthReport(
        statut=statut_global,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="2.0.0",
        services=services,
    )
