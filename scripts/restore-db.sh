#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${1:-workhub-db}"
DATABASE_NAME="${2:-workhub}"
BACKUP_PATH="${3:-}"
SA_PASSWORD="${SA_PASSWORD:-}"

if [[ -z "$SA_PASSWORD" ]]; then
  echo "SA_PASSWORD not set. Export it or pass via env." >&2
  exit 1
fi

if [[ -z "$BACKUP_PATH" || ! -f "$BACKUP_PATH" ]]; then
  echo "Backup file not found: $BACKUP_PATH" >&2
  exit 1
fi

CONTAINER_PATH="/var/opt/mssql/data/restore.bak"

echo "Copying backup into container..."
docker cp "$BACKUP_PATH" "$CONTAINER_NAME:$CONTAINER_PATH"

read -r -d '' TSQL <<'SQL'
ALTER DATABASE [workhub] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
RESTORE DATABASE [workhub] FROM DISK = '/var/opt/mssql/data/restore.bak' WITH REPLACE;
ALTER DATABASE [workhub] SET MULTI_USER;
SQL

echo "Restoring database..."
docker exec "$CONTAINER_NAME" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "$TSQL"

echo "Restore completed."

