#!/bin/sh
# Scheduler wrapper: runs backup.sh nightly at 02:30 UTC (runs loop with sleep)
set -e

while true; do
  NOW_UTC_HOUR=$(date -u +"%H")
  NOW_UTC_MIN=$(date -u +"%M")
  # run at 02:30 UTC
  if [ "$NOW_UTC_HOUR" = "02" ] && [ "$NOW_UTC_MIN" = "30" ]; then
    echo "Starting scheduled backup at $(date -u)"
    /backup/backup.sh
    if [ -f /run/secrets/backup_passphrase ]; then
      /backup/gpg_encrypt.sh
    fi
    # sleep 70 seconds to avoid double-run within the same minute
    sleep 70
  fi
  sleep 20
done
