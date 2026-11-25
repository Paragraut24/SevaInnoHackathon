from contextlib import asynccontextmanager
import logging
from pathlib import Path
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.classifier import load_classifier
from app.config import get_settings
from app.errors import error_response
from app.limiter import limiter
from app.routes.dashboard import router as dashboard_router
from app.routes.link_check import router as link_check_router
from app.routes.media_check import router as media_check_router
from app.routes.triage import router as triage_router
from app.schemas import HealthOut

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sajag.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load optional ONNX classifier once at startup and release on shutdown."""
    settings = get_settings()
    model_dir = Path(settings.ml_model_dir) if settings.ml_model_dir else None
    app.state.classifier = load_classifier(model_dir=model_dir, enabled=settings.ml_enabled)
    try:
        yield
    finally:
        app.state.classifier = None


def create_app() -> FastAPI:
    """Create stateless FastAPI app with CORS, rate limiting, localized errors and metadata-only logging."""
    settings = get_settings()
    app = FastAPI(title="Sajag API", version="0.2.0", lifespan=lifespan)
    app.state.limiter = limiter
    app.state.classifier = None

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-Lang"],
    )

    @app.middleware("http")
    async def request_metadata_middleware(request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        response.headers["x-request-id"] = request_id
        logger.info(
            "req=%s method=%s path=%s status=%s latency_ms=%s %s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            latency_ms,
            getattr(request.state, "log_extra", ""),
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        too_long = any(e["type"] == "string_too_long" for e in exc.errors())
        return error_response(request, 422, "text_too_long" if too_long else "invalid_input")

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return error_response(request, 429, "rate_limited")

    @app.exception_handler(Exception)
    async def internal_handler(request: Request, exc: Exception):
        return error_response(request, 500, "internal")

    @app.get("/api/health", response_model=HealthOut)
    def health(request: Request) -> HealthOut:
        loaded = getattr(request.app.state, "classifier", None) is not None
        return HealthOut(status="ok", ml_model="loaded" if loaded else "unavailable")

    app.include_router(triage_router)
    app.include_router(link_check_router)
    app.include_router(media_check_router)
    app.include_router(dashboard_router)
    return app


app = create_app()
