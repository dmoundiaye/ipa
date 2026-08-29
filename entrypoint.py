"""
Point d'entrée de l'application FastAPI.

Configure l'application avec:
- Logging structuré
- Rate limiting via SlowAPI
- Middleware de temps de traitement
- Tous les routers
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from core.config import settings
from core.limiter import limiter
from databases import Base, engine

# IMPORTANT:
# Import models before create_all().
# This registers all model classes with Base.metadata.
import models

# Import des routers
from routes.equipements import router as equipements_router
from routes.interfaces import router as interfaces_router
from routes.topologies import router as topologies_router
from routes.topologie_equipements import router as topologie_equipements_router
from routes.connexions import router as connexions_router
from routes.auth import router as auth_router
from routes.network_config import router as network_config_router


def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


# Configuration du logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("inventory-app")


# --------------------------------------------------
# Application lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("=" * 60)

    logger.info("ASGI application : FastAPI")
    logger.info("Web framework    : Starlette")
    logger.info("ORM              : SQLAlchemy")
    logger.info("Database URL     : %s", settings.DATABASE_URL)
    logger.info("Environment      : %s", settings.APP_ENV)

    logger.info("Creating database tables...")

    try:
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables created successfully")

    except Exception:
        logger.exception("Database initialization failed")
        raise

    logger.info("Application startup complete")

    yield

    logger.info("Application shutting down...")


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    description="API for managing network equipment, interfaces and users",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, custom_rate_limit_exceeded_handler
)
app.add_middleware(SlowAPIMiddleware)

# Middleware : temps de traitement
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    import time

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Temps-Traitement"] = f"{process_time:.3f}s"
    return response

# Inclure les routers
app.include_router(auth_router)
app.include_router(equipements_router)
app.include_router(interfaces_router)
app.include_router(topologies_router)
app.include_router(topologie_equipements_router)
app.include_router(connexions_router)
app.include_router(network_config_router)
