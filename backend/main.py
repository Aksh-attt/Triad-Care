import os
import urllib.parse
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, AsyncSessionLocal, Base
import models  # noqa: ensure models are imported for metadata
from seed import seed_database
from auth_utils import validate_jwt_configuration

from routers import auth, patients, medications, doses, appointments, followups, notifications, ai, changes

ENV = os.getenv("ENV", "development").lower()


_UNSET = object()


def validate_cors_configuration(
    env: Optional[str] = None,
    frontend_url: object = _UNSET,
    allowed_origins: object = _UNSET,
) -> list[str]:
    """Validate and return CORS allowed origins.

    In production:
    - FRONTEND_URL must be explicitly configured and non-empty.
    - All origins must use the HTTPS scheme.
    - Localhost, 127.0.0.1, ::1, and 0.0.0.0 are strictly rejected.
    - Raises RuntimeError on any invalid configuration to prevent insecure startup.
    In development/testing:
    - Defaults to localhost dev server URLs if FRONTEND_URL is not provided.
    """
    current_env = (env if env is not None else os.getenv("ENV", "development")).lower()
    f_url = frontend_url if frontend_url is not _UNSET else os.getenv("FRONTEND_URL")
    custom_origins = allowed_origins if allowed_origins is not _UNSET else os.getenv("ALLOWED_ORIGINS")

    if current_env != "production":
        dev_origins = {
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        }
        if f_url and str(f_url).strip():
            dev_origins.add(str(f_url).strip().rstrip("/"))
        if custom_origins:
            for orig in str(custom_origins).split(","):
                if orig.strip():
                    dev_origins.add(orig.strip().rstrip("/"))
        return sorted(list(dev_origins))

    # Production validation
    if not f_url or not str(f_url).strip():
        raise RuntimeError(
            "Production CORS configuration error: FRONTEND_URL must be explicitly set when ENV=production."
        )

    raw_origins = [str(f_url).strip()]
    if custom_origins:
        for orig in str(custom_origins).split(","):
            if orig.strip():
                raw_origins.append(orig.strip())

    forbidden_hosts = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
    validated = []
    for orig in raw_origins:
        parsed = urllib.parse.urlparse(orig)
        if parsed.scheme != "https":
            raise RuntimeError(
                f"Production CORS configuration error: Origin '{orig}' must use HTTPS scheme in production."
            )
        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname in forbidden_hosts or hostname.endswith(".localhost"):
            raise RuntimeError(
                f"Production CORS configuration error: Origin '{orig}' cannot use localhost or loopback addresses in production."
            )
        validated.append(f"{parsed.scheme}://{parsed.netloc}".rstrip("/"))

    return list(dict.fromkeys(validated))


@asynccontextmanager
async def lifespan(app: FastAPI):
    current_env = os.getenv("ENV", "development").lower()
    # In production, validate JWT and CORS configuration to prevent startup on misconfiguration
    if current_env == "production" or os.getenv("VALIDATE_JWT_SECRET", "false").lower() == "true":
        validate_jwt_configuration()
    if current_env == "production" or os.getenv("VALIDATE_CORS_CONFIG", "false").lower() == "true":
        validate_cors_configuration(current_env)

    if current_env != "production":
        # In development/test, create tables if not present and seed demo data
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            await seed_database(db)

    yield

    # Cleanup
    await engine.dispose()


app = FastAPI(
    title="Triad Care API",
    description="An AI-powered elderly care coordination and accountability platform connecting elderly individuals, caregivers, and family members",
    version="1.0.0",
    lifespan=lifespan,
)


# Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "img-src 'self' data: https:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "frame-ancestors 'none'"
    )
    if ENV == "production" or request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# CORS Configuration
try:
    cors_origins = validate_cors_configuration(ENV, os.getenv("FRONTEND_URL"), os.getenv("ALLOWED_ORIGINS"))
except RuntimeError:
    cors_origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(medications.router, prefix="/api/medications", tags=["Medications"])
app.include_router(doses.router, prefix="/api/doses", tags=["Doses"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(followups.router, prefix="/api/followups", tags=["Followups"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI"])
app.include_router(changes.router, prefix="/api/changes", tags=["Changes"])


@app.get("/")
async def root():
    return {"message": "Triad Care API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
