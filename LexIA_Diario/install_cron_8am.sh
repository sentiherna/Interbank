#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_CMD="cd $BASE_DIR && bash run_daily_lexia.sh --date \$(date +\\%F) >> $BASE_DIR/logs/cron_lexia_diario.log 2>&1"
CRON_LINE="0 10 * * * $CRON_CMD"

mkdir -p "$BASE_DIR/logs"

TMP_FILE="$(mktemp)"
crontab -l 2>/dev/null | grep -vF "$CRON_CMD" > "$TMP_FILE" || true
printf '%s\n' "$CRON_LINE" >> "$TMP_FILE"
crontab "$TMP_FILE"
rm -f "$TMP_FILE"

echo "Cron instalado:"
echo "$CRON_LINE"
