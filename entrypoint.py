import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.equipements import router as equipements_router
from routes.interfaces import router as interfaces_router
from routes.topologies import router as topologies_router
from routes.topologie_equipements import router as topologie_equipements_router
from routes.connexions import router as connexions_router
from routes.auth import router as auth_router

from databases import Base, engine
from core.config import settings

# IMPORTANT:
# Import models before create_all().
# This registers all model classes with Base.metadata.
import models


# --------------------------------------------------
# Logging
# --------------------------------------------------

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

app.include_router(auth_router)
app.include_router(equipements_router)
app.include_router(interfaces_router)
app.include_router(topologies_router)
app.include_router(topologie_equipements_router)
app.include_router(connexions_router)