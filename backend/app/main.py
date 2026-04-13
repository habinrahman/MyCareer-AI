import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.middleware.cache_headers import CacheControlMiddleware
from app.middleware.rate_limit import apply_rate_limit_settings, limiter
from app.middleware.slowapi_safe import SafeSlowAPIMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.utils.exceptions import AppError
from app.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level, log_json=settings.log_json)
    logger.info("startup env=%s service=%s", settings.app_env, settings.app_name)
    yield
    await engine.dispose()
    logger.info("shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()

    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.app_env,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(),
            ],
            traces_sample_rate=0.05,
            profiles_sample_rate=0.0,
        )
        logger.info("sentry_initialized")

    application = FastAPI(
        title="MyCareer AI API",
        description=(
            "Async FastAPI backend: resume upload (Supabase Storage), AI analysis "
            "(OpenAI), career chat, and report retrieval with signed URLs."
        ),
        version="0.2.0",
        lifespan=lifespan,
        debug=settings.debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS is registered after other middleware so it stays effective for preflight;
    # allow_headers uses an explicit list (not "*") because browsers reject
    # wildcard Allow-Headers together with allow_credentials=True.

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    apply_rate_limit_settings(
        enabled=settings.rate_limit_enabled,
        default_limit=settings.rate_limit_default,
    )

    # Inner → outer: first listed here runs closest to the route handler.
    application.add_middleware(
        RequestContextMiddleware,
        header_name=settings.request_id_header,
    )
    if settings.response_cache_max_age_seconds > 0:
        application.add_middleware(
            CacheControlMiddleware,
            max_age_seconds=settings.response_cache_max_age_seconds,
        )
    application.add_middleware(
        GZipMiddleware,
        minimum_size=settings.gzip_minimum_size,
    )
    # When RATE_LIMIT_ENABLED=false, limiter.enabled is False and this middleware no-ops immediately.
    application.add_middleware(SafeSlowAPIMiddleware)
    # Explicit headers: credentialed browsers reject wildcard * for Allow-Headers on some setups.
    _cors_headers = [
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        settings.request_id_header,
    ]
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=_cors_headers,
    )

    @application.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        if isinstance(exc, StarletteHTTPException):
            return await http_exception_handler(request, exc)
        logger.exception(
            "unhandled_exception path=%s",
            request.url.path,
        )
        client = sentry_sdk.get_client()
        if getattr(client, "is_enabled", lambda: False)():
            sentry_sdk.capture_exception(exc)
        if settings.debug:
            return JSONResponse(
                status_code=500,
                content={"detail": str(exc), "type": type(exc).__name__},
            )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    application.include_router(api_router)
    _attach_openapi_security(application)
    return application


def _attach_openapi_security(application: FastAPI) -> None:
    """Expose Bearer JWT in OpenAPI for manual testing (Supabase access_token)."""

    def openapi() -> dict:
        if application.openapi_schema:
            return application.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "BearerAuth"
        ] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Supabase session access_token (JWT, aud=authenticated).",
        }
        application.openapi_schema = schema
        return schema

    application.openapi = openapi  # type: ignore[method-assign]


app = create_app()
