#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
CONTAINER="${DB_CONTAINER:-aquacheck_db}"
DB_NAME="${POSTGRES_DB:-lims_db}"
DB_USER="${POSTGRES_USER:-lims_user}"

if [[ -z "${BACKUP_FILE}" ]]; then
  echo "Usage: $0 <path/to/backup.sql.gz>"
  echo ""
  echo "Available backups:"
  ls -lht "$(dirname "$0")/../backups/"*.sql.gz 2>/dev/null || echo "  (none found)"
  exit 1
fi

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Error: file not found: ${BACKUP_FILE}"
  exit 1
fi

echo "WARNING: This will drop and recreate the '${DB_NAME}' database."
read -r -p "Continue? [y/N] " confirm
[[ "${confirm}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

echo "Dropping and recreating '${DB_NAME}'..."
docker exec "${CONTAINER}" psql -U "${DB_USER}" -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';" \
  -c "DROP DATABASE IF EXISTS \"${DB_NAME}\";" \
  -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"

echo "Restoring from ${BACKUP_FILE}..."
gunzip -c "${BACKUP_FILE}" | docker exec -i "${CONTAINER}" psql -U "${DB_USER}" -d "${DB_NAME}"

echo "Restore complete."
