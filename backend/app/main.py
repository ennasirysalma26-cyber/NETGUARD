from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import create_tables
from app.routers import auth, devices, probe, interventions, alerts, topology


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="NetAdmin API",
    description="API de gestion des équipements réseau",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/v1/auth",          tags=["Auth"])
app.include_router(devices.router,       prefix="/api/v1/devices",        tags=["Devices"])
app.include_router(probe.router,         prefix="/api/v1/probe",          tags=["Probe"])
app.include_router(interventions.router, prefix="/api/v1/interventions",  tags=["Interventions"])
app.include_router(alerts.router,        prefix="/api/v1/alerts",         tags=["Alerts"])
app.include_router(topology.router,      prefix="/api/v1/topology",       tags=["Topology"])


@app.get("/")
async def root():
    return {"message": "NetAdmin API v1.0.0", "docs": "/docs"}
