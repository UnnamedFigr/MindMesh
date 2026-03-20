"""
MindMesh API — FastAPI application entry point.

YouTube Video → AI Study Guide Generator
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import sentry_sdk
import structlog
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.dependencies import get_current_user
from app.routers import guides, jobs, webhooks
from app.routers import associations, billing, reflections
from app.utils.errors import MindMeshError

# ── Structured Logging ─────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer() if get_settings().environment == "production"
        else structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


# ── Lifespan ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    settings = get_settings()

    # Init Sentry (production only)
    if settings.sentry_dsn and settings.environment == "production":
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            traces_sample_rate=0.1,
            environment=settings.environment,
        )
        logger.info("sentry.initialized")

    logger.info(
        "app.startup",
        environment=settings.environment,
        daily_spend_cap=settings.daily_spend_cap_usd,
    )

    yield

    logger.info("app.shutdown")


# ── App Factory ────────────────────────────────────────────────
def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="MindMesh API",
        description="YouTube Video → AI Study Guide Generator",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    # ── Exception Handlers ─────────────────────────────────────
    @app.exception_handler(MindMeshError)
    async def mindmesh_error_handler(request: Request, exc: MindMeshError):
        """Handle all custom MindMesh exceptions."""
        logger.warning(
            "error.handled",
            code=exc.code,
            status=exc.status_code,
            message=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.user_message,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        """Catch-all for unhandled exceptions."""
        logger.error(
            "error.unhandled",
            error=str(exc),
            path=request.url.path,
            exc_info=True,
        )
        if settings.environment == "production":
            sentry_sdk.capture_exception(exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Something went wrong. Please try again.",
                }
            },
        )

    # ── Request Logging Middleware ──────────────────────────────
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = None
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "middleware.error",
                method=request.method,
                path=request.url.path,
                error=str(exc),
                exc_info=True, # Critical for seeing the traceback
            )
            # Re-raise the exception to allow other handlers to potentially catch it
            raise

        duration_ms = (time.time() - start_time) * 1000

        if response and request.url.path not in ("/health", "/docs", "/openapi.json"):
            logger.info(
                "http.request",
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
        return response

    # ── Routers ────────────────────────────────────────────────
    app.include_router(guides.router)
    app.include_router(jobs.router)
    app.include_router(webhooks.router)
    app.include_router(associations.router)
    app.include_router(reflections.router)
    app.include_router(billing.router)
    # ── Health Check ───────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check():
        return {
            "status": "healthy",
            "version": "0.1.0",
            "environment": settings.environment,
        }

    @app.get("/api/credits", tags=["credits"])
    async def get_credits(user: dict = Depends(get_current_user)):
        """Get current user's credit status. Auto-provisions profile on first call."""
        from app.db import get_supabase
        from app.services.credits import check_credits

        user_id = user["sub"]
        supabase = get_supabase()

        # Auto-create profile if it doesn't exist (e.g. user signed up before
        # migrations were applied, so the trigger didn't fire).
        profile_res = (
            supabase.table("profiles")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if not profile_res.data:
            supabase.table("profiles").insert({
                "id": user_id,
                "email": user.get("email", ""),
                "display_name": user.get("email", "").split("@")[0],
            }).execute()

        try:
            credit_info = await check_credits(user_id, 0, supabase)
            return credit_info
        except Exception:
            return {
                "credits_used": 0,
                "daily_credit_limit": 3,
                "credits_remaining": 3,
                "tier": "core",
            }

    # ── Security Headers Middleware ──────────────────────────
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
            if settings.environment == "production":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self'; "
                    "script-src 'self'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' https://img.youtube.com https://i.ytimg.com data:; "
                    "connect-src 'self' https://*.supabase.co https://api.stripe.com; "
                    "frame-src https://checkout.stripe.com https://billing.stripe.com; "
                    "font-src 'self'"
                )
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # ── CORS (Added Last = Outer Layer) ────────────────────────
    # We add this last so it intercepts OPTIONS requests before any
    # other middleware or route validation runs.
    origins = [o.strip().rstrip("/") for o in settings.allowed_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "stripe-signature"],
        max_age=86400,
    )

    return app


# ── Application Instance ───────────────────────────────────────
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
