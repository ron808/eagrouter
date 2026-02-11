# EagRoute API — main entry point for the route optimization delivery bot system (FastAPI backend)
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import run_migrations, SessionLocal
from app.utils.data_loader import load_initial_data
from app.routers import grid_router, bots_router, orders_router, simulation_router
from app.middleware.security import SecurityMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eagroute")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup: run DB migrations (alembic), then load the CSV map data (nodes, restaurants, bots, blocked paths) into postgres
    logger.info("Starting EagRoute API...")

    run_migrations()
    logger.info("Database tables ready")

    # reads sample_data.csv and BlockedPaths.csv, creates 5 bots — safe to call multiple times, skips if data already exists
    db = SessionLocal()
    try:
        load_initial_data(db)
    finally:
        db.close()

    logger.info(f"API running - env: {settings.ENVIRONMENT}")
    logger.info("Docs available at http://localhost:8000/docs")

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Route Optimization Delivery Bot System — an eco-friendly autonomous food delivery service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# middleware runs in reverse order: security first, then CORS wraps it so CORS headers always get set even on blocked requests
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    # logs every request with how long it took — handy for spotting slow endpoints
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({ms}ms)")
    return response


# catch errors globally so we never leak raw python tracebacks to the frontend
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Bad Request", "detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again.",
        },
    )


# health check endpoints — quick way to verify the API is alive
@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "EagRoute API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# register all route groups: grid (map data), bots, orders (full CRUD), and simulation (tick-based engine)
app.include_router(grid_router, prefix="/api/grid", tags=["Grid"])
app.include_router(bots_router, prefix="/api/bots", tags=["Bots"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
