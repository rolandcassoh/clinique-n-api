#!/usr/bin/env bash
# scripts/rollback_to_laravel.sh
# ROLLBACK D'URGENCE vers le backend Laravel.
#
# À utiliser si le backend Python présente des anomalies critiques
# après le décommissionnement.
#
# Objectif : service Laravel de nouveau actif en < 30 secondes.
#
# Usage :
#   bash scripts/rollback_to_laravel.sh [staging|production]

set -euo pipefail

ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "============================================"
echo "  ROLLBACK D'URGENCE vers Laravel"
echo "  $(date)"
echo "  Environnement : ${ENV^^}"
echo "============================================"

# ── Étape 1 : Restaurer la configuration Nginx Laravel ───────────────────────
echo ""
echo "Etape 1/3 : Restauration de la config Nginx Laravel..."

LATEST_BACKUP=$(ls -t /etc/nginx/backup/clinique.conf.* 2>/dev/null | head -1 || true)

if [ -n "${LATEST_BACKUP}" ]; then
    cp "$LATEST_BACKUP" /etc/nginx/sites-available/clinique.conf
    nginx -t
    nginx -s reload
    echo "   Nginx restaure depuis : ${LATEST_BACKUP}"
else
    echo "   AVERTISSEMENT : Aucun backup Nginx trouve dans /etc/nginx/backup/"
    echo "   Restauration manuelle requise :"
    echo "     cp /path/to/laravel.conf /etc/nginx/sites-available/clinique.conf"
    echo "     nginx -s reload"
fi

# ── Étape 2 : Redémarrer le conteneur Laravel si nécessaire ──────────────────
echo ""
echo "Etape 2/3 : Redemarrage du service Laravel..."

if docker ps -a --format '{{.Names}}' | grep -q "^laravel-app$"; then
    if docker ps --format '{{.Names}}' | grep -q "^laravel-app$"; then
        echo "   Laravel deja en cours d'execution"
    else
        docker start laravel-app
        echo "   Conteneur Laravel redemarre"
    fi
else
    echo "   AVERTISSEMENT : Conteneur 'laravel-app' introuvable."
    echo "   Lancer manuellement : docker-compose up -d laravel"
fi

# ── Étape 3 : Vérification que Laravel répond ────────────────────────────────
echo ""
echo "Etape 3/3 : Verification de Laravel..."
sleep 10

if [ "$ENV" == "production" ]; then
    CHECK_URL="https://api.clinique.app/api/health"
else
    CHECK_URL="https://staging-api.clinique.app/api/health"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 15 "$CHECK_URL" 2>/dev/null || echo "000")
echo "   Statut apres rollback : HTTP ${HTTP_CODE}"

if [ "$HTTP_CODE" == "200" ]; then
    echo "   Laravel operationnel."
else
    echo "   ERREUR : Laravel ne repond pas (HTTP ${HTTP_CODE})"
    echo "   Diagnostics :"
    echo "     docker logs laravel-app --tail=100"
    echo "     docker logs nginx --tail=50"
fi

echo ""
echo "============================================"
echo "  ROLLBACK TERMINE -- ${TIMESTAMP}"
echo ""
echo "  Actions requises :"
echo "  1. Ouvrir un incident (PagerDuty / Slack #incidents)"
echo "  2. Analyser les logs Python : docker logs python-api --tail=200"
echo "  3. Documenter la cause racine avant de relancer la migration"
echo "============================================"
