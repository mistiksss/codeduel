#!/usr/bin/env bash
# Idempotent development setup for the CodeDuel Flask app.
# Safe to run repeatedly: it only creates what is missing.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

DB_NAME="code_duel"
DB_USER="codeduel"
DB_PASSWORD="54321"

echo "[install] Ensuring system packages (PostgreSQL, python venv)..."
if ! command -v pg_ctlcluster >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv postgresql postgresql-contrib
fi

echo "[install] Creating Python virtualenv and installing dependencies..."
if [ ! -x venv/bin/python ]; then
  python3 -m venv venv
fi
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install pytest

echo "[install] Starting PostgreSQL..."
sudo pg_ctlcluster "$(pg_lsclusters -h | awk 'NR==1{print $1}')" main start 2>/dev/null \
  || sudo service postgresql start 2>/dev/null || true

echo "[install] Configuring database role and schema..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
ALTER USER postgres WITH PASSWORD '${DB_PASSWORD}';
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='${DB_USER}') THEN
    CREATE ROLE ${DB_USER} LOGIN PASSWORD '${DB_PASSWORD}' CREATEDB;
  END IF;
END \$\$;
SQL

if ! sudo -u postgres psql -lqt | cut -d'|' -f1 | grep -qw "${DB_NAME}"; then
  echo "[install] Creating database ${DB_NAME} and restoring backup..."
  sudo -u postgres createdb -O postgres "${DB_NAME}"
  # The dump comes from PostgreSQL 18; strip the PG18-only SET that
  # older server versions do not recognise (harmless, keeps logs clean).
  grep -v '^SET transaction_timeout' codeduel_backup.sql \
    | sudo -u postgres psql -q -d "${DB_NAME}"
  sudo -u postgres psql -d "${DB_NAME}" <<SQL
GRANT ALL ON SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
SQL
else
  echo "[install] Database ${DB_NAME} already exists, skipping restore."
fi

if [ ! -f .env ]; then
  echo "[install] Creating .env from defaults..."
  cat > .env <<ENV
SECRET_KEY=42a1b6c9e8f7d6c5b4a3e2f1g0h9i8j7k6l5m4n3o2p1q0r9s8t7u6v5w4x3y2z1
FLASK_ENV=development
FLASK_DEBUG=1
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}
ENV
fi

echo "[install] Done."
