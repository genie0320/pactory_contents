#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$HOME/pactory_contents"
cd "$PROJECT_DIR"

LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/pipeline.log"

LOCK_FILE="/tmp/pactory_pipeline.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Another pactory pipeline instance is already running. Skipping." >> "$LOG_FILE"
    exit 0
fi

# Check if Laya model classification is currently running to avoid CPU/RAM contention
if pgrep -f "[c]lassify_laya" > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Laya mail triage model is currently executing. Deferring indexing to protect server resources." >> "$LOG_FILE"
    exit 0
fi

# Check if inbox has any files
INBOX_COUNT=$(find "$PROJECT_DIR/data/inbox" -type f | wc -l)
if [ "$INBOX_COUNT" -eq 0 ]; then
    exit 0
fi

echo "==========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Found $INBOX_COUNT new file(s) in inbox. Starting automated indexing..." >> "$LOG_FILE"

# Run Ingest with lower CPU priority (nice -n 10)
nice -n 10 "$PROJECT_DIR/.venv/bin/python" run.py ingest --move-archive >> "$LOG_FILE" 2>&1

# Run Extract with concurrency 3 to keep RAM usage under 300MB
nice -n 10 "$PROJECT_DIR/.venv/bin/python" run.py extract --concurrency 3 >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Automated indexing complete." >> "$LOG_FILE"
