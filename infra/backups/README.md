Nexudo Mail backup helpers

Files:

- backup.sh — run inside a container with network access to Postgres and read access to /var/mail and mailserver config. Produces timestamped archives under /backup.
- restore.sh — helper to restore a named backup (merge or overwrite).

Usage (via docker-compose exec or an ephemeral container):

```sh
# Create a backup (from host)
docker compose run --rm --no-deps -e PGPASSWORD=$POSTGRES_PASSWORD -v $(pwd)/infra/backups:/backup -v mail_data:/var/mail -v $(pwd)/infra/mailserver:/tmp/docker-mailserver-config backup

# Restore (from host)
docker compose run --rm --no-deps -e PGPASSWORD=$POSTGRES_PASSWORD -v $(pwd)/infra/backups:/backup -v mail_data:/var/mail -v $(pwd)/infra/mailserver:/tmp/docker-mailserver-config backup /bin/sh -c "/backup/restore.sh 20260101T120000Z overwrite"
```

Scheduled encrypted backups

1. Create a Docker secret for the backup passphrase (do NOT store the passphrase in the repo):

```sh
echo "$(openssl rand -base64 32)" > infra/backups/backup_passphrase.txt
docker secret create backup_passphrase infra/backups/backup_passphrase.txt
```

2. The `backup-scheduler` service runs daily at 02:30 UTC and will encrypt the produced archive with GPG using the passphrase from the `backup_passphrase` secret. Encrypted files are written as `<timestamp>.tar.gz.gpg` under `infra/backups`.

Notes:

- The example file `infra/backups/backup_passphrase.example` is included as a placeholder; replace it with a real secret using `docker secret create` as above.
- For production, rotate the passphrase regularly and store it in your secret manager.
