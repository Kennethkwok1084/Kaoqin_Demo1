#!/usr/bin/env bash
set -euo pipefail

# Rebuild PostgreSQL database schema using Alembic, dropping all existing objects.

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-kwok}
DB_PASSWORD=${DB_PASSWORD:-Onjuju1084}
DB_NAME=${DB_NAME:-attendence_dev}

export PGPASSWORD="$DB_PASSWORD"

echo "[1/3] Dropping and recreating schema on ${DB_HOST}:${DB_PORT}/${DB_NAME} as ${DB_USER}..."
psql -h "$DB_HOST" -U "$DB_USER" -p "$DB_PORT" -d "$DB_NAME" -v ON_ERROR_STOP=1 <<SQL
DO $$ BEGIN
  EXECUTE 'DROP SCHEMA IF EXISTS public CASCADE';
  EXECUTE 'CREATE SCHEMA public';
  EXECUTE 'GRANT ALL ON SCHEMA public TO ' || current_user || '';
END $$;
SQL

echo "[2/3] Upgrading schema via Alembic..."
cd "$(dirname "$0")/.."
alembic upgrade head

echo "[3/3] Done. Database schema rebuilt to latest migration."

