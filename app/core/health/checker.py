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
    name: str
    status: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: float
    details: dict = field(default_factory=dict)


@dataclass
class HealthReport:
    status: str
    timestamp: str
    version: str
    services: list[ServiceHealth] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "version": self.version,
            "services": [
                {
                    "name": s.name,
                    "status": s.status,
                    "latency_ms": s.latency_ms,
                    "details": s.details,
                }
                for s in self.services
            ],
        }


async def check_database() -> ServiceHealth:
    """Vérifie la connectivité à la base de données."""
    start = time.monotonic()
    try:
        from app.database import AsyncSessionLocal
        from sqlalchemy import text

        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return ServiceHealth("database", "healthy", round(latency, 2))
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        logger.warning("health.database_unhealthy", error=str(e))
        return ServiceHealth(
            "database", "unhealthy", round(latency, 2), {"error": str(e)}
        )


async def check_redis() -> ServiceHealth:
    """Vérifie la connectivité à Redis."""
    start = time.monotonic()
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        latency = (time.monotonic() - start) * 1000
        return ServiceHealth("redis", "healthy", round(latency, 2))
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        logger.warning("health.redis_degraded", error=str(e))
        return ServiceHealth(
            "redis", "degraded", round(latency, 2), {"error": str(e)}
        )


async def check_meilisearch() -> ServiceHealth:
    """Vérifie la connectivité à Meilisearch."""
    start = time.monotonic()
    try:
        import httpx

        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.meilisearch_url}/health")
        latency = (time.monotonic() - start) * 1000
        if response.status_code == 200:
            return ServiceHealth("meilisearch", "healthy", round(latency, 2))
        return ServiceHealth(
            "meilisearch",
            "degraded",
            round(latency, 2),
            {"status_code": response.status_code},
        )
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        logger.warning("health.meilisearch_degraded", error=str(e))
        return ServiceHealth(
            "meilisearch", "degraded", round(latency, 2), {"error": str(e)}
        )


async def get_health_report() -> HealthReport:
    """Effectue tous les health checks en parallèle et retourne le rapport global."""
    checks = await asyncio.gather(
        check_database(),
        check_redis(),
        check_meilisearch(),
        return_exceptions=True,
    )

    services: list[ServiceHealth] = []
    for check in checks:
        if isinstance(check, Exception):
            services.append(
                ServiceHealth("unknown", "unhealthy", 0.0, {"error": str(check)})
            )
        else:
            services.append(check)

    # Status global : unhealthy si DB down, degraded si autres services dégradés
    db_health = next((s for s in services if s.name == "database"), None)
    if db_health and db_health.status == "unhealthy":
        overall = "unhealthy"
    elif any(s.status != "healthy" for s in services):
        overall = "degraded"
    else:
        overall = "healthy"

    return HealthReport(
        status=overall,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="2.0.0",
        services=services,
    )
