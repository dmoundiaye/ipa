# Dockerfile pour l'API DevNet
# Build: docker build -t devnet-api .
# Run: docker run -p 8000:8000 --env-file .env devnet-api

FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Répertoire de travail
WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de configuration
COPY requirements.txt .
COPY entrypoint.py .
COPY app.py .
COPY main.py .
COPY schemas.py .
COPY databases.py .
COPY models.py .
COPY core/ ./core/
COPY routes/ ./routes/
COPY services/ ./services/
COPY tests/ ./tests/

# Installation des dépendances Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Création de l'utilisateur non-root
RUN useradd --create-home --shell /bin/bash app
USER app

# Expose le port
EXPOSE 8000

# Commande par défaut
CMD ["python", "-m", "uvicorn", "entrypoint:app", "--host", "0.0.0.0", "--port", "8000"]