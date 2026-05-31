#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.storage import Storage  # noqa: E402


def main() -> int:
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    username = os.environ.get("DEMO_USER", "profesor")
    password = os.environ.get("DEMO_PASSWORD", "profesor123")
    store = Storage(redis_url)
    store.ensure_user(username, password)
    print(f"Usuario demo listo: {username}", flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR al sembrar usuario demo: {exc!s}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc
