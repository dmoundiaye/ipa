"""
Configuration centralisée de l'application.

Charge les variables d'environnement depuis .env et expose
un objet Settings unique (singleton) à toute l'application.
"""
import os
from functools import lru_cache

from dotenv import load_dotenv

# Charge le .env une seule fois au démarrage
load_dotenv()


class Settings:
    """Configuration typée de l'API."""

    # ==========================================================
    # APPLICATION
    # ==========================================================
    APP_NAME: str = "Network Equipment Inventory API"
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ==========================================================
    # BASE DE DONNÉES
    # ==========================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/inventory"
    )
    SQL_ECHO: bool = os.getenv("SQL_ECHO", "false").lower() == "true"

    # ==========================================================
    # SÉCURITÉ - JWT
    # ==========================================================
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "change-me-in-production-use-openssl-rand-hex-32"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # ==========================================================
    # GNS3
    # ==========================================================
    GNS3_URL: str = os.getenv("GNS3_URL", "http://192.168.80.1:3080")
    GNS3_USERNAME: str = os.getenv("GNS3_USERNAME", "")
    GNS3_PASSWORD: str = os.getenv("GNS3_PASSWORD", "")

    # ==========================================================
    # RATE LIMITING
    # ==========================================================
    RATE_LIMIT_TOKEN: str = os.getenv("RATE_LIMIT_TOKEN", "5/minute")
    RATE_LIMIT_DEFAULT: str = os.getenv("RATE_LIMIT_DEFAULT", "100/minute")

    # ==========================================================
    # RÉSILIENCE - RETRY
    # ==========================================================
    RETRY_MAX_ATTEMPTS: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    RETRY_MIN_WAIT: int = int(os.getenv("RETRY_MIN_WAIT", "1"))
    RETRY_MAX_WAIT: int = int(os.getenv("RETRY_MAX_WAIT", "10"))

    # ==========================================================
    # LOGGING
    # ==========================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()


@lru_cache()
def get_settings() -> Settings:
    """
    Retourne l'instance unique de Settings (singleton).

    lru_cache garantit qu'on ne lit .env qu'une seule fois.
    """
    return Settings()


# Instance globale (usage direct : from core.config import settings)
settings = get_settings()
