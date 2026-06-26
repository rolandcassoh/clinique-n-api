#!/bin/bash
# Script de vérification de la santé de l'API

set -e

echo "🔍 Vérification de la santé de l'API Gestion Clinique..."
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction de vérification
check_service() {
    local name=$1
    local url=$2
    
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $name: OK"
        return 0
    else
        echo -e "${RED}✗${NC} $name: ERREUR"
        return 1
    fi
}

# Vérifier Docker Compose
if ! docker compose ps > /dev/null 2>&1; then
    echo -e "${RED}✗${NC} Docker Compose n'est pas accessible"
    exit 1
fi

# Vérifier les conteneurs
echo "📦 Statut des conteneurs:"
docker compose ps --format "table {{.Service}}\t{{.Status}}" | grep -E "api|celery|mysql|redis|meilisearch|mailhog" || true
echo ""

# Vérifier les services HTTP
echo "🌐 Vérification des endpoints:"
check_service "API Health" "http://localhost:8000/sante"
check_service "API Docs" "http://localhost:8000/docs"
check_service "Meilisearch" "http://localhost:7700/health"
check_service "MailHog UI" "http://localhost:8025"
echo ""

# Vérifier MySQL
echo "🗄️  Vérification MySQL:"
if docker compose exec -T mysql mysqladmin ping -h localhost -u root -proot > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} MySQL: OK"
else
    echo -e "${RED}✗${NC} MySQL: ERREUR"
fi

# Vérifier Redis
echo ""
echo "📮 Vérification Redis:"
if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis: OK"
else
    echo -e "${RED}✗${NC} Redis: ERREUR"
fi

echo ""
echo -e "${GREEN}✅ Vérification terminée !${NC}"
echo ""
echo "📚 Accès rapides:"
echo "   - API: http://localhost:8000/docs"
echo "   - MailHog: http://localhost:8025"
echo "   - Meilisearch: http://localhost:7700"
