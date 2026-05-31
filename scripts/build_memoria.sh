#!/bin/sh
# Genera doc/memoria.pdf desde doc/memoria.md (diagramas embebidos).
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOC="$ROOT/doc"
VENV="$ROOT/.venv/bin/python"

if ! "$VENV" -c "import markdown" 2>/dev/null; then
  "$VENV" -m pip install -q markdown
fi

cd "$DOC"

if command -v mmdc >/dev/null 2>&1; then
  MMDC=mmdc
else
  MMDC="npx -y @mermaid-js/mermaid-cli@11"
fi
# Escala 3 y ancho mayor → PNG nítidos en PDF/memoria (evitar 800px por defecto)
MMDC_SCALE="${MMDC_SCALE:-3}"
MMDC_WIDTH="${MMDC_WIDTH:-1600}"
for f in mermaid/*.mmd; do
  $MMDC -i "$f" -o "${f%.mmd}.png" -b transparent -w "$MMDC_WIDTH" -s "$MMDC_SCALE"
done
cp mermaid/clases.png diagrama-clases.png
cp mermaid/secuencia-login.png secuencia-login.png
cp mermaid/secuencia-dashboard.png secuencia-dashboard.png
cp mermaid/secuencia-vista.png secuencia-vista.png

"$VENV" - <<'PY'
import base64
import re
from pathlib import Path
import markdown

doc = Path(".")
md_text = (doc / "memoria.md").read_text(encoding="utf-8")

def embed_images(text: str) -> str:
    def repl(match):
        alt, path = match.group(1), match.group(2)
        p = doc / path
        if not p.exists():
            return match.group(0)
        data = base64.b64encode(p.read_bytes()).decode("ascii")
        mime = "image/svg+xml" if p.suffix.lower() == ".svg" else "image/png"
        return f"![{alt}](data:{mime};base64,{data})"
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, text)

html_body = markdown.markdown(embed_images(md_text), extensions=["tables", "fenced_code"])
html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Memoria — Nagasaki Analytics</title>
<style>
  body {{ font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; max-width: 820px; margin: 2rem auto; line-height: 1.45; color: #111; }}
  h1,h2,h3 {{ page-break-after: avoid; }}
  img {{ max-width: 100%; height: auto; display: block; margin: 1rem auto; }}
  em {{ color: #444; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; font-size: 0.92rem; }}
  th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.55rem; text-align: left; }}
  th {{ background: #f5f5f5; }}
  pre {{ background: #f7f7f7; padding: 0.75rem; overflow-x: auto; font-size: 0.85rem; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 2rem 0; }}
</style>
</head>
<body>{html_body}</body>
</html>"""
(doc / "memoria.html").write_text(html, encoding="utf-8")
PY

CHROMIUM=""
for c in chromium google-chrome google-chrome-stable; do
  if command -v "$c" >/dev/null 2>&1; then CHROMIUM="$c"; break; fi
done
[ -n "$CHROMIUM" ] || { echo "ERROR: hace falta chromium para generar el PDF."; exit 1; }

"$CHROMIUM" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$DOC/memoria.pdf" "file://$DOC/memoria.html"

echo "OK: $DOC/memoria.pdf"
