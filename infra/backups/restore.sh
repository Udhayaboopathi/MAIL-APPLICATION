#!/bin/sh
set -e

# Simple restore helper. Usage: restore.sh <backup-timestamp> [merge|overwrite]
if [ -z "$1" ]; then
  echo "Usage: $0 <timestamp> [merge|overwrite]"
  exit 2
fi
TS=$1
MODE=${2:-merge}
BACKUP_DIR=/backup/${TS}

if [ ! -d "${BACKUP_DIR}" ]; then
  echo "Backup not found: ${BACKUP_DIR}"
  exit 1
fi

export PGPASSWORD="${POSTGRES_PASSWORD}"
if [ -f "${BACKUP_DIR}/db.dump" ]; then
  echo "Restoring DB from ${BACKUP_DIR}/db.dump"
  pg_restore -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" --clean --if-exists "${BACKUP_DIR}/db.dump"
fi

if [ -f "${BACKUP_DIR}/maildir.tar.gz" ]; then
  echo "Restoring Maildir"
  if [ "$MODE" = "overwrite" ]; then
    rm -rf /var/mail/*
  fi
  tar -xzf "${BACKUP_DIR}/maildir.tar.gz" -C /var/mail
fi

if [ -f "${BACKUP_DIR}/dkim_keys.tar.gz" ]; then
  echo "Restoring DKIM keys"
  tar -xzf "${BACKUP_DIR}/dkim_keys.tar.gz" -C /tmp/docker-mailserver-config/opendkim
fi

echo "restore complete"
