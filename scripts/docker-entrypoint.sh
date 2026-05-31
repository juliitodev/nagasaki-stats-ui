#!/bin/sh
set -e
cd /project
python scripts/wait_for_redis.py
python scripts/seed_demo_user.py
exec "$@"
