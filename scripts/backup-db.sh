#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${1:-workhub-db}"
DATABASE_NAME="${2:-workhub}"
SA_PASSWORD="${SA_PASSWORD:-}"

if [[ -z "$SA_PASSWORD" ]]; then
  echo "SA_PASSWORD not set. Export it or pass via env." >&2
  exit 1
fi

CONTAINER_PATH="/var/opt/mssql/data/workhub-backup.bak"
OUT_FILE="backup-$(date +%Y%m%d-%H%M%S).bak"

echo "Creating backup inside container $CONTAINER_NAME ..."
docker exec "$CONTAINER_NAME" /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -C -Q "BACKUP DATABASE [$DATABASE_NAME] TO DISK = '$CONTAINER_PATH' WITH INIT" >/dev/null

echo "Copying backup to host: $OUT_FILE"
docker cp "$CONTAINER_NAME:$CONTAINER_PATH" "$OUT_FILE"

echo "Backup completed: $OUT_FILE"

