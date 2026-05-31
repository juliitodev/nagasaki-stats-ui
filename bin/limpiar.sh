#!/bin/sh
# Borra contenedores, volumen Redis e imagen local (reset completo).
set -e
BIN_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$BIN_DIR/../src/docker-compose.yml" ]; then
  ROOT="$(cd "$BIN_DIR/../src" && pwd)"
else
  ROOT="$(cd "$BIN_DIR/.." && pwd)"
fi
cd "$ROOT"
echo "AVISO: se borraran vistas, marcadores, notas y demas datos guardados."
docker compose --profile tools down -v --rmi local
