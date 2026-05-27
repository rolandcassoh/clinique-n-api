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
from app.modules.auth.api.router import router as auth_router
from app.modules.world.api.router import router as world_router
from app.modules.faq.api.router import router as faq_router
from app.modules.blog.api.router import router as blog_router
from app.modules.page.api.router import router as page_router
from app.modules.tag.api.router import router as tag_router
from app.modules.slider.api.router import router as slider_router
from app.modules.currency.api.router import router as currency_router
from app.modules.language.api.router import router as language_router
from app.modules.constant.api.router import router as constant_router
# Phase 2 — Commerce
from app.modules.customer.api.router import router as customer_router
from app.modules.promotion.api.router import router as promotion_router
from app.modules.tax.api.router import router as tax_router
from app.modules.product.api.router import router as product_router
from app.modules.service.api.router import router as service_router
from app.modules.request_service.api.router import router as request_service_router
from app.modules.logistic.api.router import router as logistic_router
# Phase 3 — Clinique
from app.modules.clinic.api.router import router as clinic_router
from app.modules.vital.api.router import router as vital_router
from app.modules.subscription.api.router import router as subscription_router
# Phase 4 — Cœur médical
from app.modules.appointment.api.router import router as appointment_router
from app.modules.appointment.api.webhooks import webhook_router
from app.modules.encounter.api.router import router as encounter_router
from app.modules.billing.api.router import router as billing_router
from app.modules.wallet.api.router import router as wallet_router
from app.modules.commission.api.router import router as commission_router
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
    logger.info("application.startup", env=settings.app_env)
    yield
    await close_redis()
    logger.info("application.shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
    lifespan=lifespan,
)

# --- Middleware (outermost first) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(StructuredLoggingMiddleware)

# --- Prometheus ---
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# --- Routers ---
app.include_router(auth_router)

# Phase 1 — Référentiels
app.include_router(world_router, prefix="/api", tags=["World"])

app.include_router(faq_router, prefix="/api", tags=["FAQ"])
app.include_router(blog_router, prefix="/api", tags=["Blog"])
app.include_router(page_router, prefix="/api", tags=["Pages"])
app.include_router(tag_router, prefix="/api", tags=["Tags"])
app.include_router(slider_router, prefix="/api", tags=["Sliders"])
app.include_router(currency_router, prefix="/api", tags=["Currencies"])
app.include_router(language_router, prefix="/api", tags=["Languages"])
app.include_router(constant_router, prefix="/api", tags=["Constants"])

# Phase 2 — Commerce
app.include_router(customer_router, prefix="/api", tags=["Customer"])
app.include_router(promotion_router, prefix="/api", tags=["Promotions"])
app.include_router(tax_router, prefix="/api", tags=["Taxes"])
app.include_router(product_router, prefix="/api", tags=["Products"])
app.include_router(service_router, prefix="/api", tags=["Services"])
app.include_router(request_service_router, prefix="/api", tags=["Request Services"])
app.include_router(logistic_router, prefix="/api", tags=["Logistics"])

# Phase 3 — Clinique
app.include_router(clinic_router, prefix="/api", tags=["Clinic"])
app.include_router(vital_router, prefix="/api", tags=["Vitals"])
app.include_router(subscription_router, prefix="/api", tags=["Subscriptions"])

# Phase 4 — Cœur médical
app.include_router(appointment_router, prefix="/api", tags=["Appointments"])
app.include_router(webhook_router, prefix="/api", tags=["Webhooks"])
app.include_router(encounter_router, prefix="/api", tags=["Encounters"])
app.include_router(billing_router, prefix="/api", tags=["Billing"])
app.include_router(wallet_router, prefix="/api", tags=["Wallet"])
app.include_router(commission_router, prefix="/api", tags=["Commissions"])


# --- Global exception handler for domain errors ---
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "env": settings.app_env}
