#!/bin/sh
# Para contenedores sin borrar vistas/marcadores/notas guardados en Redis.
set -e
BIN_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$BIN_DIR/../src/docker-compose.yml" ]; then
  ROOT="$(cd "$BIN_DIR/../src" && pwd)"
else
  ROOT="$(cd "$BIN_DIR/.." && pwd)"
fi
cd "$ROOT"
docker compose --profile tools down
