#!/bin/sh
set -e

# Simple backup script for single-node deployments.
# Produces a timestamped archive with DB dump (custom format) + Maildir tarball + DKIM keys if present.

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
OUTDIR=/backup/${TIMESTAMP}
mkdir -p "${OUTDIR}"

: "Exporting Postgres DB"
export PGPASSWORD="${POSTGRES_PASSWORD}"
pg_dump -h "${POSTGRES_HOST:-postgres}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -F c -f "${OUTDIR}/db.dump"

: "Archiving Maildir"
tar -czf "${OUTDIR}/maildir.tar.gz" -C /var/mail .

: "Including DKIM keys if present"
if [ -d /tmp/docker-mailserver/opendkim ] || [ -d /tmp/docker-mailserver-config/opendkim ]; then
  if [ -d /tmp/docker-mailserver-config/opendkim ]; then
    tar -czf "${OUTDIR}/dkim_keys.tar.gz" -C /tmp/docker-mailserver-config/opendkim .
  elif [ -d /tmp/docker-mailserver/opendkim ]; then
    tar -czf "${OUTDIR}/dkim_keys.tar.gz" -C /tmp/docker-mailserver/opendkim .
  fi
fi

echo "backup completed: ${OUTDIR}"
