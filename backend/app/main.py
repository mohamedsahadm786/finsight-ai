"""
FinSight AI — Main FastAPI Application

This is the entry point for the entire backend. It:
1. Creates the FastAPI application instance
2. Registers all API routers (auth, documents, jobs, reports, chat, admin, superadmin)
3. Configures CORS middleware (allows the React frontend to call the API)
4. Adds Prometheus metrics instrumentation
5. Adds rate limiting (slowapi)
6. Runs startup tasks (MinIO bucket creation)
7. Provides a health check endpoint

To run locally:
    uvicorn backend.app.main:app --reload --port 8000

Then visit:
    http://localhost:8000/docs  — Swagger UI (interactive API docs)
    http://localhost:8000/redoc — ReDoc (alternative API docs)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.app.api.admin import router as admin_router
from backend.app.api.auth import router as auth_router
from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.reports import router as reports_router
from backend.app.api.superadmin import router as superadmin_router
from backend.app.config import get_settings
from backend.app.dependencies.rate_limit import limiter


# ── Startup and Shutdown Events ───────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs when the application starts up and shuts down.

    Startup:
    - Ensure MinIO bucket exists (creates it if missing)

    Shutdown:
    - Clean up any open connections
    """
    # ── STARTUP ──
    settings = get_settings()
    print(f"Starting FinSight AI in {settings.APP_ENV} mode...")

    # Ensure MinIO bucket exists
    try:
        from backend.app.services.storage_service import ensure_bucket_exists
        ensure_bucket_exists()
        print("MinIO bucket verified.")
    except Exception as e:
        print(f"Warning: MinIO bucket check failed: {e}")
        print("MinIO may not be running. Document upload will fail.")

    print("FinSight AI is ready!")
    print(f"  Swagger UI: http://localhost:8000/docs")
    print(f"  ReDoc:      http://localhost:8000/redoc")

    yield  # App is now running and serving requests

    # ── SHUTDOWN ──
    print("Shutting down FinSight AI...")


# ── Create FastAPI App ────────────────────────────────────────────

app = FastAPI(
    title="FinSight AI",
    description=(
        "Financial Document Intelligence & Credit Risk Advisory Platform. "
        "Upload financial PDFs and receive AI-powered credit risk analysis "
        "with ratio extraction, sentiment analysis, breach detection, "
        "ML risk scoring with SHAP explainability, and RAG-powered chat."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",      # Swagger UI
    redoc_url="/redoc",    # ReDoc
)


# ── Rate Limiting ─────────────────────────────────────────────────
# Attach the limiter to the app so it can access request state.
# The actual rate limits are applied per-endpoint using decorators.

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── CORS Middleware ───────────────────────────────────────────────
# This allows the React frontend (running on localhost:5173 during
# development) to make API calls to the FastAPI backend (localhost:8000).
# Without CORS, the browser would block these cross-origin requests.

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server (React)
        "http://localhost:3000",   # Alternative React port
        "http://localhost:8000",   # Same origin
    ],
    allow_credentials=True,        # Allow cookies (for refresh tokens)
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all headers (including Authorization)
)


# ── Prometheus Metrics ────────────────────────────────────────────
# This automatically instruments ALL endpoints with:
# - Request count per endpoint
# - Request latency histogram per endpoint
# - Response size per endpoint
# Metrics are available at GET /metrics

Instrumentator().instrument(app).expose(app)


# ── Register API Routers ──────────────────────────────────────────
# Each router handles a group of related endpoints.
# The prefix from each router (e.g., "/auth", "/documents") is
# combined with the individual route paths.

app.include_router(auth_router)          # /auth/*
app.include_router(documents_router)     # /documents/*
app.include_router(jobs_router)          # /jobs/*
app.include_router(reports_router)       # /reports/*
app.include_router(chat_router)          # /chat/*
app.include_router(admin_router)         # /admin/*
app.include_router(superadmin_router)    # /superadmin/*


# ── Health Check ──────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """
    Simple health check endpoint.

    Used by:
    - Docker health checks to verify the container is running
    - Kubernetes liveness probes
    - Load balancers to check if the server is responding
    - Monitoring systems to detect downtime
    """
    return {
        "status": "healthy",
        "service": "finsight-ai",
        "version": "1.0.0",
    }