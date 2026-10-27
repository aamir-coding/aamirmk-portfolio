import logging
import re
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.chat import router as chat_router
from app.api.health import router as health_router
from app.settings import Settings, get_settings

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
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    )
    logger.info("Starting up application in %s environment", settings.ENVIRONMENT)
    yield
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

    # Pure ASGI path normalization middleware (runs before routing)
    app.add_middleware(NormalizePathMiddleware)

    # Request ID and access logging middleware
    @app.middleware("http")
    async def request_id_and_logging_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id

        # Read client IP (honoring X-Forwarded-For if available)
        forwarded_for = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else "unknown")
        )

        logger.info(
            "[%s] %s %s status=%d duration=%.2fms ip=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            client_ip,
        )
        return response

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
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation error in request payload",
                    "details": exc.errors(),
                    "request_id": request_id,
                }
            },
            headers={"X-Request-ID": request_id} if request_id else None,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        logger.exception("[%s] Unhandled exception: %s", request_id, str(exc))
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
    app.include_router(chat_router, prefix="/api")

    return app


app = create_app()
