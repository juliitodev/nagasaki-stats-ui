#!/bin/sh
# Empaqueta nagasaki-stats-ui para entrega ALS (estructura Veriprac).
# Uso: ./scripts/pack_als.sh ALS_proyecto-Apellido1_Apellido2_Nombre-12345678X
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NAME="${1:?Indica el nombre del ZIP, p. ej. ALS_proyecto-Garcia_Lopez_Manuel-12345678X}"
STAGING="/tmp/${NAME}"
INNER="${STAGING}/${NAME}"
DOC_SRC="$ROOT/doc"

case "$NAME" in
  *REEMPLAZAR*) echo "ERROR: sustituye REEMPLAZAR por tus apellidos, nombre y DNI."; exit 1 ;;
esac

rm -rf "$STAGING"
mkdir -p "${INNER}/src" "${INNER}/doc" "${INNER}/bin"

rsync -a "$ROOT/" "${INNER}/src/" \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '.pytest_cache' \
  --exclude 'als-entrega' \
  --exclude '.git' \
  --exclude '*.pyc' \
  --exclude '*.zip' \
  --exclude 'doc/memoria.html'

cp -r "$ROOT/bin/"* "${INNER}/bin/" 2>/dev/null || true

cp "$DOC_SRC/info.txt" "${INNER}/doc/" 2>/dev/null || true
[ -f "$DOC_SRC/memoria.pdf" ] && cp "$DOC_SRC/memoria.pdf" "${INNER}/doc/"

for img in diagrama-clases.png secuencia-login.png secuencia-dashboard.png secuencia-vista.png; do
  [ -f "$DOC_SRC/$img" ] && cp "$DOC_SRC/$img" "${INNER}/doc/"
done

[ -f "$DOC_SRC/mermaid/clases.png" ] && [ ! -f "${INNER}/doc/diagrama-clases.png" ] && \
  cp "$DOC_SRC/mermaid/clases.png" "${INNER}/doc/diagrama-clases.png"
for s in secuencia-login secuencia-dashboard secuencia-vista; do
  [ -f "$DOC_SRC/mermaid/${s}.png" ] && [ ! -f "${INNER}/doc/${s}.png" ] && \
    cp "$DOC_SRC/mermaid/${s}.png" "${INNER}/doc/"
done

echo "--- Contenido doc/ ---"
ls -la "${INNER}/doc/"

if [ ! -f "${INNER}/doc/memoria.pdf" ]; then
  echo ""
  echo "AVISO: falta doc/memoria.pdf — ejecuta ./scripts/build_memoria.sh"
fi
if grep -q 'REEMPLAZAR' "${INNER}/doc/info.txt" 2>/dev/null; then
  echo "AVISO: rellena doc/info.txt antes de subir."
fi

(cd "$STAGING" && zip -r "${NAME}.zip" "$NAME")
echo ""
echo "Creado: ${STAGING}/${NAME}.zip"
echo "Asunto del envío: ${NAME}"
