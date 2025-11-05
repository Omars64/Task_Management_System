#!/bin/sh

set -e

host="${DB_HOST:-mssql}"
port="${DB_PORT:-1433}"
user="${DB_USER:-sa}"
pass="${DB_PASS:-}"

# Resolve sqlcmd path
sqlcmd_path() {
  if [ -x "/opt/mssql-tools18/bin/sqlcmd" ]; then
    echo "/opt/mssql-tools18/bin/sqlcmd"
  elif [ -x "/opt/mssql-tools/bin/sqlcmd" ]; then
    echo "/opt/mssql-tools/bin/sqlcmd"
  else
    echo ""
  fi
}

SQLCMD="$(sqlcmd_path)"

echo "Waiting for SQL Server at ${host}:${port} to be ready..."

if [ -n "${SQLCMD}" ]; then
  # Wait for sqlcmd to be able to run a query
  until ${SQLCMD} -S "${host},${port}" -U "${user}" -P "${pass}" -C -Q "SELECT 1" >/dev/null 2>&1; do
    echo "Waiting for SQL Server to accept queries..."
    sleep 2
  done
else
  # Fallback: try simple TCP connect using nc if available, else sleep a bit
  if command -v nc >/dev/null 2>&1; then
    until nc -z "${host}" "${port}" >/dev/null 2>&1; do
      echo "Waiting for TCP ${host}:${port}..."
      sleep 2
    done
  else
    # Blind wait
    sleep 15
  fi
fi

echo "MSSQL is ready — starting application."
exec "$@"
