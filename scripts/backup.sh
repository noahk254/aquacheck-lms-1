#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${DB_CONTAINER:-aquacheck_db}"
DB_NAME="${POSTGRES_DB:-lims_db}"
DB_USER="${POSTGRES_USER:-lims_user}"
BACKUP_DIR="$(cd "$(dirname "$0")/../backups" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT="${BACKUP_DIR}/manual_${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "Backing up '${DB_NAME}' from container '${CONTAINER}'..."
docker exec "${CONTAINER}" pg_dump -U "${DB_USER}" --schema=public "${DB_NAME}" \
  | gzip -6 > "${OUTPUT}"

echo "Backup saved: ${OUTPUT}"
echo "Size: $(du -sh "${OUTPUT}" | cut -f1)"
