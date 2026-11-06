#!/usr/bin/env bash
# Daily Backup Script for Pactory Seed Engine
set -euo pipefail

BASE_DIR="$HOME/pactory_contents"
BACKUP_DIR="$BASE_DIR/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/pactory_backup_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting daily backup..."

# 1. Back up database, processed texts/metadata, my_corpus, and configuration
cd "$BASE_DIR"
tar -czf "$BACKUP_FILE" \
    --exclude="data/inbox/*" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".pytest_cache" \
    data/index/catalog.db \
    data/my_corpus \
    data/processed/metadata \
    data/processed/texts \
    .env 2>/dev/null || true

echo "[$(date)] Backup created at $BACKUP_FILE ($(du -h "$BACKUP_FILE" 2>/dev/null | cut -f1 || echo 'done'))"

# 2. Rotate backups: retain only last 14 days
echo "[$(date)] Pruning backups older than 14 days..."
find "$BACKUP_DIR" -name "pactory_backup_*.tar.gz" -mtime +14 -delete

echo "[$(date)] Backup process completed successfully."
