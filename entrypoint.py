import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from routes.equipements import router as equipements_router

from databases import Base, engine

# IMPORTANT:
# Import models before create_all().
# This registers all model classes with Base.metadata.
import models


# --------------------------------------------------
# Logging
# --------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("inventory-app")


# --------------------------------------------------
# Application lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("=" * 60)
    logger.info("Starting Network Equipment Inventory API")
    logger.info("=" * 60)

    logger.info("ASGI application : FastAPI")
    logger.info("Web framework    : Starlette")
    logger.info("ORM              : SQLAlchemy")
    logger.info("Database URL     : %s", os.getenv("DATABASE_URL"))

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
    title="Network Equipment Inventory API",
    description="API for managing network equipment, interfaces and users",
    version=os.getenv("APP_VERSION", "1.0.0"),
    lifespan=lifespan,
)

app.include_router(equipements_router)