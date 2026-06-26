import time
import uuid
from collections.abc import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = structlog.get_logger()


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        identifiant_requete = str(uuid.uuid4())
        debut = time.perf_counter()

        log = logger.bind(
            request_id=identifiant_requete,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "inconnu",
        )

        log.info("requete.demarree")

        try:
            reponse = await call_next(request)
        except Exception as exc:
            log.exception("requete.echouee", error=str(exc))
            raise

        duree_ms = round((time.perf_counter() - debut) * 1000, 2)
        log.info(
            "requete.terminee",
            status_code=reponse.status_code,
            duration_ms=duree_ms,
        )

        reponse.headers["X-Request-ID"] = identifiant_requete
        return reponse
