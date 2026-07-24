#!/usr/bin/env bash
# Wrapper portable para el pipeline original.
# En modo local puede quedar sin credenciales AWS; si existe config/credentials.sh,
# se carga desde alli para ejecuciones en S3/prod.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$BASE_DIR/config/credentials.sh" ]; then
  # shellcheck disable=SC1091
  source "$BASE_DIR/config/credentials.sh"
fi
