#!/bin/sh
set -eu

BACKUP_FILE="${BACKUP_FILE:-/backups/lpdb_backup.dump}"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

pg_restore \
    --host="${DATABASE_HOST:-db}" \
    --port="${DATABASE_PORT:-5432}" \
    --username="${DATABASE_USER:-postgres}" \
    --dbname="${DATABASE_NAME:-lpdb}" \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    --exit-on-error \
    "$BACKUP_FILE"

echo "Database restore completed successfully."
