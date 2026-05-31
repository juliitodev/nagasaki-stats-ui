#!/bin/sh
# Arranca Nagasaki Analytics (bin/ → raíz del proyecto o ../src en el ZIP ALS).
set -e
BIN_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$BIN_DIR/../src/docker-compose.yml" ]; then
  ROOT="$(cd "$BIN_DIR/../src" && pwd)"
else
  ROOT="$(cd "$BIN_DIR/.." && pwd)"
fi
cd "$ROOT"
echo "Arrancando desde: $ROOT"
echo "Web: http://localhost:3080  (profesor / profesor123)"
exec docker compose up --build "$@"
