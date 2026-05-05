# Server and DNS Setup

This repository runs behind Traefik and expects a few environment variables to define the public hostnames.

## 1. Server prerequisites

Use a Linux VPS with:

- Docker Engine
- Docker Compose v2
- Open ports: `80`, `443`, `25`, `587`, `993`
- Optional admin port: `8080` for the Traefik dashboard

Recommended firewall example:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 25/tcp
sudo ufw allow 587/tcp
sudo ufw allow 993/tcp
sudo ufw allow 8080/tcp
```

## 2. Environment values

Set these in `.env` before starting the stack:

```env
ROOT_DOMAIN=sudoinnovation.tech
WEB_DOMAIN=sudoinnovation.tech
API_DOMAIN=api.sudoinnovation.tech
MAIL_DOMAIN=mail.sudoinnovation.tech
SMTP_HOSTNAME=mail.sudoinnovation.tech
TRAEFIK_ACME_EMAIL=admin@sudoinnovation.tech
```

Other important values already used by the stack:

- `DATABASE_URL` points to `pgbouncer:6432`
- `REDIS_URL` points to `redis:6379`
- `NEXT_PUBLIC_API_BASE_URL` should point to the public API URL in production

## 3. DNS records

# Server and DNS Setup

This file is the single step-by-step setup guide for the server, DNS, local development, and production deployment.

## 1. What this stack includes

- Mail layer: docker-mailserver, Postfix, Dovecot, Rspamd
- Backend: FastAPI, PostgreSQL, Redis, Celery
- Frontend: Next.js App Router
- Edge: Traefik

## 2. Server prerequisites

Use a Linux VPS with:

- Docker Engine
- Docker Compose v2
- Open ports: `80`, `443`, `25`, `587`, `993`
- Optional admin port: `8080` for the Traefik dashboard

Recommended firewall example:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 25/tcp
sudo ufw allow 587/tcp
sudo ufw allow 993/tcp
sudo ufw allow 8080/tcp
```

## 3. Environment values

Create `.env` from `.env.example` and set the public hostnames:

```env
POSTGRES_DB=nexudo_mail
POSTGRES_USER=nexudo
ROOT_DOMAIN=sudoinnovation.tech
WEB_DOMAIN=sudoinnovation.tech
API_DOMAIN=api.sudoinnovation.tech
MAIL_DOMAIN=mail.sudoinnovation.tech
SMTP_HOSTNAME=mail.sudoinnovation.tech
SMTP_PORT=587
NEXT_PUBLIC_API_BASE_URL=https://api.sudoinnovation.tech
NEXT_PUBLIC_APP_NAME=Nexudo Mail
ENVIRONMENT=production
TRAEFIK_ACME_EMAIL=admin@sudoinnovation.tech
```

Other important values used by the stack:

- `DATABASE_URL` points to `pgbouncer:6432`
- `REDIS_URL` points to `redis:6379`
- `JWT_SECRET`, `JWT_REFRESH_SECRET`, and `ENCRYPTION_KEY` must be set

## 4. DNS records

Create these DNS records for your domain.

| Type  | Name           | Value                                                               | Notes                              |
| ----- | -------------- | ------------------------------------------------------------------- | ---------------------------------- |
| A     | `@`            | your server IPv4                                                    | Frontend root domain               |
| A     | `api`          | your server IPv4                                                    | Backend API                        |
| A     | `mail`         | your server IPv4                                                    | Mail server                        |
| MX    | `@`            | `mail.sudoinnovation.tech`                                          | Mail delivery                      |
| TXT   | `@`            | `v=spf1 mx ip4:YOUR_SERVER_IP -all`                                 | Basic sender policy                |
| TXT   | `_dmarc`       | `v=DMARC1; p=quarantine; rua=mailto:postmaster@sudoinnovation.tech` | DMARC policy                       |
| CNAME | `autoconfig`   | `mail.sudoinnovation.tech`                                          | Optional mail client auto-config   |
| CNAME | `autodiscover` | `mail.sudoinnovation.tech`                                          | Optional mail client auto-discover |

If your DNS provider does not support CNAME at the root, use an `A` record for `@`.

## 5. Clone and configure

```bash
git clone https://github.com/Udhayaboopathi/MAIL-APPLICATION.git
cd MAIL-APPLICATION

mkdir -p secrets

openssl rand -base64 32 > secrets/JWT_SECRET
openssl rand -base64 32 > secrets/JWT_REFRESH_SECRET
openssl rand -base64 32 > secrets/ENCRYPTION_KEY
echo "your-strong-db-password-here" > secrets/POSTGRES_PASSWORD
echo "postgresql+asyncpg://nexudo:your-strong-db-password-here@pgbouncer:6432/nexudo_mail" > secrets/DATABASE_URL
echo "redis://redis:6379/0" > secrets/REDIS_URL
chmod 400 secrets/*
```

Use this `.env` layout for local development or production, then change only the values that differ:

```env
POSTGRES_DB=nexudo_mail
POSTGRES_USER=nexudo
POSTGRES_PASSWORD=nexudo_password
DATABASE_URL=postgresql+asyncpg://nexudo:nexudo_password@pgbouncer:6432/nexudo_mail
REDIS_URL=redis://redis:6379/0
JWT_SECRET=change-me
JWT_REFRESH_SECRET=change-me-too
JWT_ACCESS_TOKEN_MINUTES=30
JWT_REFRESH_TOKEN_DAYS=30
SMTP_HOSTNAME=mail.sudoinnovation.tech
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=nexudo_sk_xxx
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Nexudo Mail
TRAEFIK_ACME_EMAIL=admin@sudoinnovation.tech
DOMAIN=sudoinnovation.tech
CLOUDFLARE_API_TOKEN=
```

## 6. Start the stack locally

1. Copy `.env.example` to `.env` if you have not already done so.
2. Start the full stack.

```bash
docker compose up --build
```

3. Open the frontend at `http://localhost:3000` and the API at `http://localhost:8000`.
4. If you are running the backend on Windows or want the initial super-admin credentials on disk, set `INITIAL_ADMIN_OUTPUT` to a writable local path before starting the stack.

Windows example:

```powershell
$env:INITIAL_ADMIN_OUTPUT="C:\Users\Udhay\Desktop\initial_super_admin.txt"
```

## 7. Start the stack in production

```bash
docker compose up -d --build
docker compose logs -f backend
```

The startup will:

1. Validate all required secrets and fail fast if they are missing or too short.
2. Connect to PostgreSQL and Redis.
3. Start the backend, frontend, Traefik, Celery worker, and Celery beat.
4. Request Let's Encrypt certificates for the public domains.

## 8. Verify deployment

```bash
docker compose ps
curl -I https://api.yourdomain.com/health
curl -I https://yourdomain.com
```

Expected public routes:

- `https://yourdomain.com`
- `https://api.yourdomain.com`
- `https://mail.yourdomain.com`

## 9. Initial admin provisioning

If `ENVIRONMENT=development` (default), the backend auto-creates a super-admin on first run:

```bash
export ENVIRONMENT=development
docker compose up -d --build
docker compose logs backend | grep -i "admin"
```

The generated credentials are written to `/tmp/initial_super_admin.txt` inside the backend container. Retrieve them with:

```bash
docker compose exec backend cat /tmp/initial_super_admin.txt
```

On Windows or any local non-container run, point `INITIAL_ADMIN_OUTPUT` to a writable path before starting the backend so the file is created on the host instead.

For production (`ENVIRONMENT=production`), the auto-create feature is disabled. You must insert a super-admin manually after migrations:

```bash
docker compose exec postgres psql -U nexudo -d nexudo_mail -c \
  "INSERT INTO users (email, password_hash, role, created_at, updated_at) \
  VALUES ('admin@sudoinnovation.tech', '<bcrypt_hash>', 'SUPER_ADMIN', NOW(), NOW());"
```

## 10. Mail notes

For mail delivery to work well, also configure:

- Reverse DNS (PTR) for the server IP to `mail.sudoinnovation.tech`
- SPF, DKIM, and DMARC records
- Port `25` open if you want to receive mail from external servers

Without PTR and DKIM, inbox placement will be poor.

## 11. Backups

Backups run daily at 02:30 UTC.

```bash
openssl rand -base64 16 > infra/backups/backup_passphrase
chmod 400 infra/backups/backup_passphrase
docker compose down && docker compose up -d
```

Manual backup:

```bash
docker compose run --rm backup /backup/backup.sh
ls -lh infra/backups/
```

Manual restore:

```bash
docker compose run --rm backup /backup/restore.sh 20260501T023000Z overwrite
```

## 12. SMTP API key integration

Create an SMTP API key as a super-admin and use it with your mail client or integrations.

## 13. Common issues

- If startup fails with secret validation errors, confirm `JWT_SECRET`, `JWT_REFRESH_SECRET`, `ENCRYPTION_KEY`, `POSTGRES_PASSWORD`, `DATABASE_URL`, and `REDIS_URL` are set.
- If `docker compose exec` fails on Windows, Docker Desktop is not running or not installed.
- If mail delivery is poor, verify PTR, SPF, DKIM, and DMARC.
- [ ] NEXT_PUBLIC_API_BASE_URL points to the public API domain (https://api.sudoinnovation.tech)
- [ ] Initial super-admin created (via DB insert or one-time endpoint)
- [ ] Database migrations applied
- [ ] Redis connectivity verified
- [ ] PgBouncer connection pooling configured and tested

### TLS & Traefik

- [ ] Traefik ACME challenge configured (httpChallenge or dnsChallenge)
- [ ] Let's Encrypt certificates auto-issued (check traefik_letsencrypt volume)
- [ ] HTTPS routes accessible (curl -I https://api.sudoinnovation.tech)
- [ ] Traefik dashboard accessible at https://sudoinnovation.tech:8080 (if open)

### Mail Flow

- [ ] SMTP relay from backend to mailserver working
- [ ] Test send: create domain, create mailbox, send test email
- [ ] Test receive: check mailserver logs for incoming mail delivery
- [ ] DKIM signatures present in outgoing mail headers

### Logs & Monitoring

- [ ] Backend startup shows no errors (docker compose logs backend)
- [ ] Frontend builds and serves successfully
- [ ] Celery worker and beat tasks running
- [ ] Health endpoints return OK (curl https://api.sudoinnovation.tech/health)

### Backup & Recovery

- [ ] Backup scheduler running (docker compose logs backup-scheduler)
- [ ] Backup passphrase secret created
- [ ] Test restore procedure

## 11. Troubleshooting

### Startup secret check fails

If the backend fails on startup with a message like "Startup secret checks failed: JWT_SECRET is missing...", ensure:

1. Secret files exist in `./secrets/` with proper names.
2. Docker secrets are declared in `docker-compose.yml` under the `secrets:` top-level section.
3. Services have `secrets:` list in their definition.
4. Secret values are not empty and meet minimum length.

```bash
# Check that backend container can read secrets
docker compose exec backend ls -la /run/secrets/
```

### Let's Encrypt certificate fails

If Traefik fails to issue certificates:

1. Verify DNS resolves to the server IP.
2. Ensure port 80 is open for the HTTP-01 challenge.
3. Check Traefik logs: `docker compose logs traefik`.
4. Review the ACME email in `.env` (TRAEFIK_ACME_EMAIL).

### Mail delivery issues

If mail is not being delivered or received:

1. Check mailserver logs: `docker compose logs mailserver`.
2. Verify SPF, DKIM, and DMARC records are present.
3. Test with `mail:` command inside the container: `docker compose exec mailserver mail`.
4. Check relay configuration in docker-mailserver (if using relay mode).

## 12. Security Reminders

1. **Secrets**: Always use Docker secrets or a secret manager in production. Never commit `.env` files with real values.
2. **TLS**: Ensure all communication is encrypted (HTTPS, TLS). Use HSTS headers.
3. **Firewall**: Restrict admin ports (8080 for Traefik) to your IP range.
4. **Backups**: Test backup and restore procedures regularly.
5. **Updates**: Keep Docker images and dependencies up to date. Monitor CVE lists.
6. **Logs**: Aggregate and monitor application and system logs for anomalies.
