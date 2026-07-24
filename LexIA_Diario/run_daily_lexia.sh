#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"
LOCK_FILE="$LOG_DIR/lexia_diario.lock"

# El calendario operativo se interpreta en horario de Buenos Aires salvo configuracion explicita.
export TZ="${LEXIA_TIMEZONE:-America/Argentina/Buenos_Aires}"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Otra corrida de LexIA ya esta en curso; se omite esta ejecucion."
  exit 0
fi

load_env_clean() {
  local env_file="$1"
  if [ -f "$env_file" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(sed 's/\r$//' "$env_file")
    set +a
  fi
}

load_env_clean "$BASE_DIR/config/.env_email"
load_env_clean "$BASE_DIR/config/reference.env"
load_env_clean "$BASE_DIR/config/github.env"
load_env_clean "$BASE_DIR/config/groq.env"
load_env_clean "$BASE_DIR/config/credentials.sh"

export STORAGE_MODE="${STORAGE_MODE:-local}"
SEND_FAILURE_EMAIL=1
for arg in "$@"; do
  if [ "$arg" = "--no-email" ]; then
    SEND_FAILURE_EMAIL=0
  fi
done

PYTHON_BIN="$BASE_DIR/.venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="python3"
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/lexia_diario_${STAMP}.log"

notify_failure() {
  local status="$1"
  if [ "$SEND_FAILURE_EMAIL" -eq 0 ] || [ -z "${REPORT_EMAIL_TO:-}" ] || [ -z "${SMTP_USER:-}" ] || [ -z "${SMTP_PASSWORD:-}" ]; then
    return 0
  fi

  "$PYTHON_BIN" - "$status" "$LOG_FILE" <<'PY' || true
import os
import smtplib
import sys
from email.message import EmailMessage
from pathlib import Path

status, log_path = sys.argv[1], Path(sys.argv[2])
msg = EmailMessage()
msg["Subject"] = f"ERROR LexIA Normativo Diario (exit {status})"
msg["From"] = os.getenv("SMTP_FROM", os.environ["SMTP_USER"])
msg["To"] = os.environ["REPORT_EMAIL_TO"]
msg.set_content("La corrida diaria de LexIA finalizo con error. Se adjunta el log para su revision.")
if log_path.exists():
    msg.add_attachment(log_path.read_bytes(), maintype="text", subtype="plain", filename=log_path.name)
with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587"))) as smtp:
    smtp.starttls()
    smtp.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    smtp.send_message(msg)
PY
}

on_error() {
  local status=$?
  trap - ERR
  echo "LexIA finalizo con error (exit $status)."
  notify_failure "$status"
  exit "$status"
}

trap on_error ERR
cd "$BASE_DIR"
"$PYTHON_BIN" daily_lexia.py "$@" 2>&1 | tee "$LOG_FILE"
trap - ERR
