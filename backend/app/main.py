import asyncio
import hashlib
import hmac
import logging
import re
import secrets
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import async_sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.chat import router as chat_router
from app.api.context import router as context_router
from app.api.debug import router as debug_router
from app.api.evals import router as evals_router
from app.api.fit import router as fit_router
from app.api.health import router as health_router
from app.api.operations import router as operations_router
from app.companies import load_company_contexts
from app.db.analytics import AnalyticsWriter
from app.db.session import create_database_engine
from app.fit.cache import ReportCache, cache_identity
from app.llm import GroqLLM
from app.logging_config import JsonLogFormatter
from app.release import load_release
from app.safety.ip import get_client_ip
from app.safety.middleware import RequestBoundsMiddleware
from app.safety.rate_limiter import SlidingWindowRateLimiter
from app.settings import Settings, get_settings
from app.tools.registry import ToolRegistry

logger = logging.getLogger("app")


class NormalizePathMiddleware:
    """Pure ASGI middleware that normalizes duplicate slashes in request paths."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            path = scope.get("path", "")
            if "//" in path:
                scope["path"] = re.sub(r"/+", "/", path)
        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan management for startup and shutdown tasks."""
    settings = getattr(app.state, "settings", get_settings())
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        handlers=[handler],
    )
    for name in ("groq", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logger.info("Starting up application in %s environment", settings.ENVIRONMENT)
    try:
        from app.retrieval.dense import ensure_model_cached
        from app.retrieval.retriever import get_retriever

        await asyncio.to_thread(ensure_model_cached)
        retriever = await asyncio.to_thread(get_retriever)
        await retriever.retrieve("engineering experience", top_k=1)
        app.state.retrieval_ready = True
        logger.info("Hybrid retrieval index initialized and ready")
    except Exception as exc:
        logger.warning("Retriever startup unavailable: %s", type(exc).__name__)

    # Auto-authorize boot-bound inference capacity if configured or in production
    auto_authorize = settings.AUTO_AUTHORIZE_INFERENCE or (
        settings.ENVIRONMENT == "production" and bool(settings.GROQ_API_KEY)
    )
    if auto_authorize and getattr(app.state, "llm", None) is not None:
        try:
            from datetime import UTC, datetime, timedelta

            from app.safety.admission import Allowance

            now = datetime.now(UTC)
            midnight = datetime.combine(
                now.date() + timedelta(days=1), datetime.min.time(), UTC
            )
            shared = settings.INFERENCE_SHARED_LIMITS
            allowance = Allowance(
                boot_id=app.state.llm.ledger.boot_id,
                verified_at=now,
                expires_at=midnight,
                requests=shared.rpd,
                tokens=shared.tpd,
            )
            app.state.llm.ledger.authorize(allowance, warm_up_seconds=0.0)
            logger.info(
                "Inference capacity authorized for boot %s (requests=%d, tokens=%d)",
                allowance.boot_id,
                allowance.requests,
                allowance.tokens,
            )
        except Exception as exc:
            logger.warning("Inference auto-authorization skipped or failed: %s", exc)
    database = None
    analytics = None
    try:
        if settings.DATABASE_URL.get_secret_value():
            database = create_database_engine(settings.DATABASE_URL)
            sessions = async_sessionmaker(database, expire_on_commit=False)
            app.state.db_sessions = sessions
            key = settings.ANALYTICS_IP_HASH_KEY.get_secret_value()
            if key:
                analytics = AnalyticsWriter(sessions, key.encode())
                app.state.analytics = analytics
        yield
    finally:
        try:
            if analytics is not None:
                await analytics.close()
        finally:
            app.state.analytics = None
            app.state.db_sessions = None
            try:
                if database is not None:
                    await database.dispose()
            finally:
                await app.state.llm.aclose()
        logger.info("Shutting down application")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory for FastAPI app instance."""
    app_settings = settings or get_settings()

    app = FastAPI(
        title="Aamir Mohammed Khan - AI Assistant API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.release = load_release()
    app.state.company_contexts = load_company_contexts()
    app.state.db_sessions = None
    app.state.analytics = None
    app.state.retrieval_ready = False
    app.state.log_ip_salt = secrets.token_bytes(32)
    app.state.llm = GroqLLM(app_settings)
    app.state.tool_registry = ToolRegistry()
    app.state.fit_cache = ReportCache(
        identity=cache_identity(
            (app_settings.LLM_MODEL_MAIN, app_settings.LLM_MODEL_UTILITY)
        )
    )
    app.state.chat_rate_limiter = SlidingWindowRateLimiter(
        requests_per_window=app_settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        enabled=app_settings.RATE_LIMIT_ENABLED,
        max_keys=app_settings.RATE_LIMIT_MAX_KEYS,
    )
    app.state.fit_rate_limiter = SlidingWindowRateLimiter(
        requests_per_window=app_settings.FIT_RATE_LIMIT_DAILY,
        window_seconds=86400,
        enabled=app_settings.RATE_LIMIT_ENABLED,
        max_keys=app_settings.RATE_LIMIT_MAX_KEYS,
    )
    app.state.ops_rate_limiter = SlidingWindowRateLimiter(
        requests_per_window=30,
        max_keys=2,
    )
    app.dependency_overrides[get_settings] = lambda: app_settings

    # Pure ASGI path normalization middleware (runs before routing)
    app.add_middleware(NormalizePathMiddleware)

    # Request ID, security headers, and access logging middleware
    @app.middleware("http")
    async def request_id_and_logging_middleware(request: Request, call_next):
        candidate_id = request.headers.get("X-Request-ID", "")
        request_id = (
            candidate_id
            if re.fullmatch(r"[a-fA-F0-9]{32}", candidate_id)
            else uuid.uuid4().hex
        )
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if (
            request.url.path.startswith("/api/ops/")
            or request.url.path == "/api/health"
        ):
            response.headers["Cache-Control"] = "no-store"

        client_ip = get_client_ip(request)
        ip_hash = hmac.new(
            app.state.log_ip_salt, client_ip.encode(), hashlib.sha256
        ).hexdigest()[:24]
        route = getattr(request.scope.get("route"), "path", "<unmatched>")
        method = (
            request.method if request.method in {"GET", "POST", "OPTIONS"} else "OTHER"
        )

        logger.info(
            "[%s] %s %s status=%d duration=%.2fms ip_hash=%s",
            request_id,
            method,
            route,
            response.status_code,
            duration_ms,
            ip_hash,
        )
        return response

    # Body-read disconnects must return outside BaseHTTPMiddleware's call_next.
    app.add_middleware(
        RequestBoundsMiddleware, max_bytes=app_settings.MAX_REQUEST_BYTES
    )

    # CORS configuration with explicit allowlist (no wildcards)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Consistent JSON error handlers
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", None)
        headers = dict(exc.headers) if exc.headers else {}
        if request_id:
            headers["X-Request-ID"] = request_id

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "request_id": request_id,
                    **(
                        {"state": "resting"}
                        if headers.get("X-Assistant-State") == "resting"
                        else {}
                    ),
                }
            },
            headers=headers if headers else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation error in request payload",
                    "details": [
                        {
                            key: value
                            for key, value in error.items()
                            if key not in {"ctx", "input"}
                        }
                        for error in exc.errors()
                    ],
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.error("[%s] Unhandled exception: %s", request_id, type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    # Mount API routers
    app.include_router(health_router, prefix="/api")
    app.include_router(context_router, prefix="/api")
    app.include_router(operations_router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(fit_router, prefix="/api")
    app.include_router(debug_router, prefix="/api")
    app.include_router(evals_router, prefix="/api")

    return app


app = create_app()
