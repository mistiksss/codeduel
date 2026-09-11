#!/usr/bin/env bash
# Per-boot startup: ensure PostgreSQL is running before the app starts.
set -euo pipefail

sudo pg_ctlcluster "$(pg_lsclusters -h | awk 'NR==1{print $1}')" main start 2>/dev/null \
  || sudo service postgresql start 2>/dev/null || true

# Wait until PostgreSQL accepts connections.
for _ in $(seq 1 30); do
  if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
    echo "[start] PostgreSQL is ready."
    break
  fi
  sleep 1
done
