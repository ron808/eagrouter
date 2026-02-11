# app entry point
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
    # runs on startup and shutdown
    logger.info("Starting EagRoute API...")

    # let alembic handle all schema creation/updates
    run_migrations()
    logger.info("Database tables ready")

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
    description="Route Optimization Delivery Bot System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# middleware order matters! fastapi runs them in reverse order of how
# they're added, so security goes first, then cors wraps around it.
# this way cors headers always get set, even on rate-limited responses.
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
    # logs request info + how long it took
    start = time.time()
    response = await call_next(request)
    ms = round((time.time() - start) * 1000, 2)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({ms}ms)")
    return response


# global error handlers so we never leak raw tracebacks to the client
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


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "EagRoute API is running", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


# routers
app.include_router(grid_router, prefix="/api/grid", tags=["Grid"])
app.include_router(bots_router, prefix="/api/bots", tags=["Bots"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])
app.include_router(simulation_router, prefix="/api/simulation", tags=["Simulation"])
