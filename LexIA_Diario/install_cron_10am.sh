#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$BASE_DIR/logs/cron_lexia_diario.log"
MARKER="run_daily_lexia.sh"
CRON_LINE="0 10 * * * cd $BASE_DIR && bash run_daily_lexia.sh --date \$(TZ=America/Argentina/Buenos_Aires date +\\%F) >> $LOG_FILE 2>&1"

mkdir -p "$BASE_DIR/logs"
{ crontab -l 2>/dev/null | grep -vF "$MARKER" || true; printf '%s\n' "$CRON_LINE"; } | crontab -
echo "Cron LexIA instalado: todos los dias a las 10:00 (America/Argentina/Buenos_Aires)."
