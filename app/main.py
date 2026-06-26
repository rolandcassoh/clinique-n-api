from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.core.cache.redis_client import close_redis
from app.core.middleware.logging import StructuredLoggingMiddleware
from app.core.middleware.security import SecurityHeadersMiddleware
from app.modules.auth.api.routeur import router as auth_router
from app.modules.monde.api.routeur import router as world_router
from app.modules.faq.api.routeur import router as faq_router
from app.modules.blog.api.routeur import router as blog_router
from app.modules.page.api.routeur import router as page_router
from app.modules.etiquette.api.routeur import router as tag_router
from app.modules.slider.api.routeur import router as slider_router
from app.modules.devise.api.routeur import router as currency_router
from app.modules.langue.api.routeur import router as language_router
from app.modules.constante.api.routeur import router as constant_router
# Phase 2 — Commerce (module marchand)
from app.modules.client.api.routeur import router as customer_router
from app.modules.promotion.api.routeur import router as promotion_router
from app.modules.taxe.api.routeur import router as tax_router
from app.modules.produit.api.routeur import router as product_router
from app.modules.service.api.routeur import router as service_router
from app.modules.demande_service.api.routeur import router as request_service_router
from app.modules.logistique.api.routeur import router as logistic_router
# Phase 3 — Clinique
from app.modules.clinic.api.routeur import router as clinic_router
from app.modules.signe_vital.api.routeur import router as vital_router
from app.modules.abonnement.api.routeur import router as subscription_router
# Phase 4 — Cœur médical
from app.modules.rendez_vous.api.routeur import router as appointment_router
from app.modules.rendez_vous.api.webhooks import webhook_router
from app.modules.consultation.api.routeur import router as encounter_router
from app.modules.facturation.api.routeur import router as billing_router
from app.modules.portefeuille.api.routeur import router as wallet_router
from app.modules.commission.api.routeur import router as commission_router
from app.shared.exceptions.domain import DomainException

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.app_env == "development"
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("application.demarrage", env=settings.app_env)
    yield
    await close_redis()
    logger.info("application.arret")


app = FastAPI(
    titre=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    lifespan=lifespan,
)

# --- Middlewares (du plus externe au plus interne) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(StructuredLoggingMiddleware)

# --- Métriques Prometheus ---
Instrumentator().instrument(app).expose(app, endpoint="/metriques")

# --- Routeurs de l'application ---
app.include_router(auth_router)

# Phase 1 — Référentiels (données de base)
app.include_router(world_router, prefix="/api", tags=["Monde"])

app.include_router(faq_router, prefix="/api", tags=["FAQ"])
app.include_router(blog_router, prefix="/api", tags=["Blog"])
app.include_router(page_router, prefix="/api", tags=["Pages"])
app.include_router(tag_router, prefix="/api", tags=["Étiquettes"])
app.include_router(slider_router, prefix="/api", tags=["Sliders"])
app.include_router(currency_router, prefix="/api", tags=["Devises"])
app.include_router(language_router, prefix="/api", tags=["Langues"])
app.include_router(constant_router, prefix="/api", tags=["Constantes"])

# Phase 2 — Commerce
app.include_router(customer_router, prefix="/api", tags=["Clients"])
app.include_router(promotion_router, prefix="/api", tags=["Promotions"])
app.include_router(tax_router, prefix="/api", tags=["Taxes"])
app.include_router(product_router, prefix="/api", tags=["Produits"])
app.include_router(service_router, prefix="/api", tags=["Services"])
app.include_router(request_service_router, prefix="/api", tags=["Demandes de service"])
app.include_router(logistic_router, prefix="/api", tags=["Logistique"])

# Phase 3 — Clinique
app.include_router(clinic_router, prefix="/api", tags=["Clinique"])
app.include_router(vital_router, prefix="/api", tags=["Signes vitaux"])
app.include_router(subscription_router, prefix="/api", tags=["Abonnements"])

# Phase 4 — Cœur médical
app.include_router(appointment_router, prefix="/api", tags=["Rendez-vous"])
app.include_router(webhook_router, prefix="/api", tags=["Webhooks"])
app.include_router(encounter_router, prefix="/api", tags=["Consultations"])
app.include_router(billing_router, prefix="/api", tags=["Facturation"])
app.include_router(wallet_router, prefix="/api", tags=["Portefeuille"])
app.include_router(commission_router, prefix="/api", tags=["Commissions"])


# --- Gestionnaire global des erreurs de domaine ---
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    return JSONResponse(status_code=400, contenu={"detail": exc.message})


@app.get("/sante", tags=["Système"])
async def verification_etat() -> dict[str, str]:
    """Vérification de l'état de l'application."""
    return {"statut": "ok", "env": settings.app_env}
