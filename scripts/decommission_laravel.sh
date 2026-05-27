#!/usr/bin/env bash
# scripts/decommission_laravel.sh
# Décommissionnement progressif et sécurisé du service Laravel.
#
# Pré-requis :
#   - Le backend Python est déployé et répond sur /health
#   - Les backups sont configurés (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME)
#   - Accès root ou sudo sur le serveur Nginx
#
# Usage :
#   bash scripts/decommission_laravel.sh [staging|production]
#
# Rollback d'urgence :
#   bash scripts/rollback_to_laravel.sh [staging|production]

set -euo pipefail

ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "============================================"
echo "  DECOMMISSIONNEMENT LARAVEL -- ${ENV^^}"
echo "  $(date)"
echo "============================================"

# ── Étape 1/6 : Vérification que le backend Python est opérationnel ───────────
echo ""
echo "Etape 1/6 : Verification du backend Python..."

if [ "$ENV" == "production" ]; then
    HEALTH_URL="https://api.clinique.app/health"
else
    HEALTH_URL="https://staging-api.clinique.app/health"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$HTTP_CODE" != "200" ]; then
    echo "ERREUR : Le backend Python ne repond pas (HTTP ${HTTP_CODE})"
    echo "   URL testee : ${HEALTH_URL}"
    echo "   Abandon du decommissionnement. Corriger le probleme et relancer."
    exit 1
fi
echo "   Backend Python operationnel (HTTP 200)"

# ── Étape 2/6 : Backup final du code et des données Laravel ──────────────────
echo ""
echo "Etape 2/6 : Backup final du code Laravel..."
bash "${SCRIPT_DIR}/backup_laravel.sh" "$ENV"
echo "   Backup cree avec succes"

# ── Étape 3/6 : Vérification du taux d'erreur (Prometheus) ──────────────────
echo ""
echo "Etape 3/6 : Verification des metriques (taux d'erreur HTTP 5xx)..."

ERROR_RATE=$(curl -s \
    "http://prometheus:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[5m])" \
    | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    result = d['data']['result']
    print(result[0]['value'][1] if result else '0')
except Exception:
    print('0')
" 2>/dev/null || echo "0")

if python3 -c "import sys; sys.exit(0 if float('${ERROR_RATE}') < 0.01 else 1)" 2>/dev/null; then
    echo "   Taux d'erreur acceptable : ${ERROR_RATE} req/s"
else
    echo "   AVERTISSEMENT : Taux d'erreur eleve (${ERROR_RATE} req/s)."
    printf "   Proceder quand meme ? (y/N) : "
    read -r CONFIRM
    [[ "${CONFIRM}" == "y" ]] || { echo "Abandon. Corriger les erreurs avant de poursuivre."; exit 1; }
fi

# ── Étape 4/6 : Basculement Nginx vers Python à 100% ────────────────────────
echo ""
echo "Etape 4/6 : Basculement Nginx vers Python (100%)..."

if [ "$ENV" == "production" ]; then
    # Sauvegarder la config courante avant modification
    mkdir -p /etc/nginx/backup
    cp /etc/nginx/sites-available/clinique.conf \
       "/etc/nginx/backup/clinique.conf.${TIMESTAMP}"
    echo "   Config Nginx sauvegardee : /etc/nginx/backup/clinique.conf.${TIMESTAMP}"

    # Déployer la config production Python
    cp "${SCRIPT_DIR}/../nginx/nginx.conf" /etc/nginx/sites-available/clinique.conf

    # Tester et recharger Nginx
    nginx -t
    nginx -s reload
    echo "   Nginx reconfigure et rechargé"
else
    echo "   [STAGING] Simulation du basculement Nginx (dry-run)"
    nginx -t -c "${SCRIPT_DIR}/../nginx/nginx.conf" 2>/dev/null && \
        echo "   [STAGING] Config Nginx valide" || \
        echo "   [STAGING] AVERTISSEMENT : erreur de syntaxe dans nginx.conf"
fi

# ── Étape 5/6 : Arrêt progressif du service Laravel ─────────────────────────
echo ""
echo "Etape 5/6 : Arret du service Laravel..."

if [ "$ENV" == "production" ]; then
    # Arrêt gracieux : attendre les connexions en cours (30s)
    docker stop --time 30 laravel-app 2>/dev/null || true
    docker rm laravel-app 2>/dev/null || true
    echo "   Service Laravel arrete et supprime"
else
    echo "   [STAGING] Simulation de l'arret Laravel (dry-run)"
fi

# ── Étape 6/6 : Vérification finale ─────────────────────────────────────────
echo ""
echo "Etape 6/6 : Verification finale..."
sleep 5

FINAL_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$HEALTH_URL" 2>/dev/null || echo "000")

if [ "$FINAL_CODE" == "200" ]; then
    echo "   Systeme operationnel apres decommissionnement (HTTP 200)"
else
    echo "   PROBLEME DETECTE apres decommissionnement (HTTP ${FINAL_CODE})"
    echo "   Lancer le rollback d'urgence :"
    echo "     bash ${SCRIPT_DIR}/rollback_to_laravel.sh ${ENV}"
    exit 1
fi

echo ""
echo "============================================"
echo "  DECOMMISSIONNEMENT TERMINE -- ${TIMESTAMP}"
echo "  Surveiller les metriques pendant 30 min."
echo "============================================"
