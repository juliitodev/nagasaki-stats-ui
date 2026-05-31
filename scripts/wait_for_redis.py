#!/usr/bin/env python3
"""Espera a que Redis acepte conexiones antes de arrancar Flask (Docker Compose)."""
from __future__ import annotations

import os
import sys
import time
from urllib.parse import urlparse

import redis


def main() -> int:
    url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    parsed = urlparse(url)
    host = parsed.hostname or "redis"
    port = parsed.port or 6379
    db = int((parsed.path or "/0").lstrip("/") or "0")
    deadline = time.time() + float(os.environ.get("REDIS_WAIT_SECONDS", "90"))

    print(f"Esperando Redis en {host}:{port} (db {db})…", flush=True)
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
            client.ping()
            print("Redis listo.", flush=True)
            return 0
        except Exception as exc:
            last_err = exc
            time.sleep(2)

    print(
        "ERROR: no se pudo conectar a Redis.\n"
        "  - Arranca el stack completo: docker compose up --build\n"
        "  - Deben estar activos los servicios 'redis' y 'nagasaki-analytics'\n"
        f"  - Último error: {last_err!s}",
        file=sys.stderr,
        flush=True,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
