#!/bin/sh
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOC="$ROOT/doc"
ERR=0

warn() { echo "AVISO: $1"; }
fail() { echo "ERROR: $1"; ERR=1; }

echo "=== Verificación entrega ALS ==="

if [ ! -f "$DOC/info.txt" ]; then
  fail "Falta doc/info.txt"
elif grep -q 'REEMPLAZAR' "$DOC/info.txt" 2>/dev/null; then
  fail "Rellena doc/info.txt (quedan campos REEMPLAZAR)"
fi

if [ ! -f "$DOC/memoria.pdf" ]; then
  fail "Falta doc/memoria.pdf — ./scripts/build_memoria.sh"
else
  echo "OK: memoria.pdf"
fi

BIN="$ROOT/bin"
if [ ! -f "$BIN/LEEME.txt" ]; then
  fail "Falta bin/LEEME.txt"
elif [ ! -x "$BIN/arrancar.sh" ]; then
  fail "Falta o no es ejecutable bin/arrancar.sh"
else
  echo "OK: bin/ (LEEME.txt, arrancar.sh, arrancar.bat)"
fi

for img in diagrama-clases.png secuencia-login.png secuencia-dashboard.png secuencia-vista.png; do
  if [ ! -f "$DOC/$img" ]; then
    warn "Falta doc/$img"
  else
    echo "OK: $img"
  fi
done

if [ -x "$ROOT/.venv/bin/pytest" ]; then
  "$ROOT/.venv/bin/pytest" -q "$ROOT/tests" || fail "pytest falló"
  echo "OK: tests"
elif command -v pytest >/dev/null 2>&1; then
  pytest -q "$ROOT/tests" || fail "pytest falló"
  echo "OK: tests"
else
  warn "pytest no disponible"
fi

if [ "$ERR" -eq 1 ]; then
  echo ""
  echo "Corrige los ERROR antes del ZIP."
  exit 1
fi
echo ""
echo "Listo: ./scripts/pack_als.sh ALS_proyecto-Apellido1_Apellido2_Nombre-12345678X"
