#!/usr/bin/env bash

set -euo pipefail

host="${DB_HOST:-mssql}"
port="${DB_PORT:-1433}"
user="${DB_USER:-sa}"
pass="${DB_PASS:-}"

# helper to test sqlcmd in either possible install path
sqlcmd_path() {
  if [ -x "/opt/mssql-tools18/bin/sqlcmd" ]; then
    echo "/opt/mssql-tools18/bin/sqlcmd"
  elif [ -x "/opt/mssql-tools/bin/sqlcmd" ]; then
    echo "/opt/mssql-tools/bin/sqlcmd"
  else
    echo ""
  fi
}

echo "Waiting for ${host}:${port} to accept TCP connections..."

# Wait for TCP port using bash /dev/tcp (portable and avoids netcat flags)
until bash -c "cat < /dev/tcp/${host}/${port}" >/dev/null 2>&1; do
  >&2 echo "Waiting for MSSQL TCP..."
  sleep 1
done

# If sqlcmd present, verify SQL Server accepts logins and queries
SQLCMD="$(sqlcmd_path)"
if [ -n "${SQLCMD}" ]; then
  echo "Found sqlcmd at ${SQLCMD} — verifying SQL connectivity..."
  until "${SQLCMD}" -S "${host},${port}" -U "${user}" -P "${pass}" -Q "SELECT 1" >/dev/null 2>&1; do
    >&2 echo "SQL Server not ready for queries yet..."
    sleep 1
  done
fi

echo "MSSQL is ready — starting application."

# exec the container CMD (so signals pass to the app)
exec "$@"