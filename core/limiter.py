"""
Module centralisé pour le rate limiter.

Évite les imports circulaires entre entrypoint et les routers.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.config import settings


# Rate limiter (singleton partagé par toute l'application)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT_DEFAULT],
    strategy="fixed-window",
)
