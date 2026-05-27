#!/usr/bin/env bash
# scripts/backup_laravel.sh
# Sauvegarde complète du code et des données Laravel avant décommissionnement.
# Usage : bash scripts/backup_laravel.sh [staging|production]

set -euo pipefail

ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/laravel/${TIMESTAMP}"

mkdir -p "$BACKUP_DIR"

echo "Backup Laravel -> ${BACKUP_DIR}"
echo "Environnement : ${ENV}"
echo "Timestamp     : ${TIMESTAMP}"
echo ""

# ── Backup du code source (hors vendor/node_modules/logs) ─────────────────────
echo "Archivage du code source Laravel..."
tar -czf "${BACKUP_DIR}/laravel_code_${TIMESTAMP}.tar.gz" \
    --exclude='vendor' \
    --exclude='node_modules' \
    --exclude='storage/logs' \
    --exclude='.git' \
    /var/www/laravel/ 2>/dev/null || {
        echo "AVERTISSEMENT : archivage partiel (certains fichiers inaccessibles)"
    }

# ── Backup de la base de données ──────────────────────────────────────────────
echo "Dump de la base de donnees MySQL..."
mysqldump \
    --single-transaction \
    --routines \
    --triggers \
    --add-drop-table \
    -h "${DB_HOST:-localhost}" \
    -u "${DB_USER:-root}" \
    -p"${DB_PASSWORD:-}" \
    "${DB_NAME:-clinique_db}" \
    > "${BACKUP_DIR}/database_${TIMESTAMP}.sql" 2>/dev/null || {
        echo "ERREUR : echec du dump MySQL. Verifier DB_HOST, DB_USER, DB_PASSWORD, DB_NAME."
        exit 1
    }

# ── Backup des fichiers uploadés (storage) ────────────────────────────────────
echo "Archivage du storage (uploads, medias)..."
tar -czf "${BACKUP_DIR}/storage_${TIMESTAMP}.tar.gz" \
    /var/www/laravel/storage/app/public/ 2>/dev/null || {
        echo "AVERTISSEMENT : storage partiellement sauvegarde"
    }

# ── Checksum de vérification ──────────────────────────────────────────────────
echo "Generation des checksums SHA256..."
sha256sum "${BACKUP_DIR}"/*.tar.gz "${BACKUP_DIR}"/*.sql \
    > "${BACKUP_DIR}/checksums.sha256" 2>/dev/null || true

echo ""
echo "Backup termine : ${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}/"
