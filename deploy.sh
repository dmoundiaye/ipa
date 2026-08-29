#!/bin/bash
# Script de déploiement automatique pour DevNet API
# Usage: ./deploy.sh [dev|prod]

set -e

ENV=${1:-dev}

echo "=========================================="
echo "Déploiement DevNet API - Environnement: $ENV"
echo "=========================================="

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que Docker est installé
if ! command -v docker &> /dev/null; then
    log_error "Docker n'est pas installé. Veuillez l'installer."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose n'est pas installé. Veuillez l'installer."
    exit 1
fi

# Vérifier le fichier .env
if [ ! -f .env ]; then
    log_warn "Fichier .env non trouvé. Création à partir de .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
    else
        log_error "Impossible de créer .env"
        exit 1
    fi
fi

# Construire et lancer les services
log_info "Construction des images Docker..."
docker-compose build

log_info "Démarrage des services..."
docker-compose up -d

# Attendre que l'API soit prête
log_info "Vérification de l'état de l'API..."
sleep 5

# Vérifier si l'API répond
for i in {1..30}; do
    if curl -s http://localhost:8000/docs &> /dev/null; then
        log_info "API DevNet opérationnelle!"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "L'API ne répond pas après 30 tentatives"
        docker-compose logs
        exit 1
    fi
    echo "Attente de l'API... ($i/30)"
    sleep 2
done

# Afficher le statut
echo ""
echo "=========================================="
echo "Services actifs:"
echo "=========================================="
docker-compose ps

echo ""
echo "=========================================="
echo "URLs d'accès:"
echo "=========================================="
echo "API:     http://localhost:8000"
echo "Docs:    http://localhost:8000/docs"
echo "Redoc:   http://localhost:8000/redoc"

# Commandes utiles
echo ""
echo "=========================================="
echo "Commandes utiles:"
echo "=========================================="
echo "Logs:     docker-compose logs -f api"
echo "Restart:  docker-compose restart api"
echo "Stop:    docker-compose down"
echo "Clean:   docker-compose down -v"

log_info "Déploiement terminé avec succès!"
