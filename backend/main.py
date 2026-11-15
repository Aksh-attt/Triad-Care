import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from database import engine, AsyncSessionLocal, Base
import models  # noqa: ensure models are imported for metadata
from seed import seed_database

from routers import auth, patients, medications, doses, appointments, followups, notifications, ai, changes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed demo data if DB is empty
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

# CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = list(set([
    frontend_url,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
