# Nagasaki Analytics

Consola web Flask para analizar series de sensores simulados (plantas solares, tráfico). Usa Jinja2, Flask-Login, Sirope/Redis y un catálogo demo embebido.

Documentación completa en [`doc/memoria.md`](doc/memoria.md) (arranque, evaluación, entrega ALS).

## Arranque

```bash
docker compose up --build
```

http://localhost:3080 — `profesor` / `profesor123`

## Arranque sin Docker

```bash
redis-server &
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=src.app REDIS_URL=redis://localhost:6379/0
flask run --host 0.0.0.0 --port 3080
```

## Datos demo

```bash
python scripts/generate_demo_seed.py
```

35 entidades, 36 puntos por serie → `src/data/demo_seed.json`.

## Tests

```bash
pytest -q
```

## Entrega ALS

Rellena `doc/info.txt`, genera el PDF con `./scripts/build_memoria.sh`, verifica con `./scripts/verificar_entrega.sh` y empaqueta con `./scripts/pack_als.sh`. Detalle en [`doc/memoria.md`](doc/memoria.md), sección 10.

## TFG

Este repo es la práctica de ALS y, a la vez, el panel de analítica de mi TFG Nagasaki. Para evaluar ALS no hace falta el resto del TFG. Explicación en [`doc/memoria.md`](doc/memoria.md), sección 1.
