#!/bin/sh
set -e

# Encrypt latest backup directory into a .tar.gz.gpg using GPG symmetric encryption
BACKUP_ROOT=/backup
LATEST=$(ls -1t ${BACKUP_ROOT} | head -n1)
if [ -z "${LATEST}" ]; then
  echo "no backup found"
  exit 0
fi
INPATH="${BACKUP_ROOT}/${LATEST}"
OUTFILE="${INPATH}.tar.gz"

echo "Packing ${INPATH} -> ${OUTFILE}"
tar -czf "${OUTFILE}" -C "${INPATH}" .

if [ -f /run/secrets/backup_passphrase ]; then
  PASSPHRASE_FILE=/run/secrets/backup_passphrase
  echo "Encrypting ${OUTFILE} with GPG symmetric"
  apk add --no-cache gnupg >/dev/null 2>&1 || true
  gpg --batch --yes --pinentry-mode loopback --passphrase-file "${PASSPHRASE_FILE}" -c "${OUTFILE}"
  if [ -f "${OUTFILE}.gpg" ]; then
    rm -f "${OUTFILE}"
    echo "Encrypted to ${OUTFILE}.gpg"
  fi
else
  echo "No passphrase secret found; leaving unencrypted archive"
fi
