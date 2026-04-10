#!/bin/sh
set -e

POSTGRES_USER="${DB_USER:-cognitoruser}"
POSTGRES_PASSWORD="${DB_PASSWORD:-cognitorpassword}"
POSTGRES_DB="${DB_NAME:-cognitor}"
PGDATA="${PGDATA:-/var/lib/postgresql/data}"
PGROOT="$(dirname "$PGDATA")"

mkdir -p /run/postgresql
chown postgres:postgres /run/postgresql
chmod 775 /run/postgresql

mkdir -p "$PGROOT" "$PGDATA"
chown -R postgres:postgres "$PGROOT"
chmod 700 "$PGDATA"

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  su-exec postgres initdb -D "$PGDATA"
fi

su-exec postgres pg_ctl -D "$PGDATA" -o "-c listen_addresses='127.0.0.1' -p ${DB_PORT:-5432}" -w start

if ! su-exec postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'" | grep -q 1; then
  su-exec postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE \"${POSTGRES_USER}\" WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}';"
else
  su-exec postgres psql -v ON_ERROR_STOP=1 -c "ALTER ROLE \"${POSTGRES_USER}\" WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}';"
fi

if ! su-exec postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'" | grep -q 1; then
  su-exec postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"${POSTGRES_DB}\" OWNER \"${POSTGRES_USER}\";"
fi

shutdown() {
  su-exec postgres pg_ctl -D "$PGDATA" -m fast stop
}

trap shutdown INT TERM EXIT

node apps/backend/dist/main.js &
BACKEND_PID=$!

npm run start --workspace=apps/frontend &
FRONTEND_PID=$!

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  wait "$BACKEND_PID"
  EXIT_CODE=$?
else
  wait "$FRONTEND_PID"
  EXIT_CODE=$?
fi

kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true

exit "$EXIT_CODE"
