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

## 4. Compose service mapping

The stack expects these public hostnames:

- Frontend: `WEB_DOMAIN`
- API: `API_DOMAIN`
- Mail host: `MAIL_DOMAIN`

Traefik routes traffic using the labels in `docker-compose.yml`, and TLS certificates are issued automatically through Let’s Encrypt using `TRAEFIK_ACME_EMAIL`.

## 5. Deployment order

1. Update `.env` with your real domain values.
2. Point DNS records to the server IP.
3. Start the stack:

```bash
docker compose up -d --build
```

4. Check Traefik, backend, and frontend logs.
5. Verify HTTPS routes:
   - `https://sudoinnovation.tech`
   - `https://api.sudoinnovation.tech`

## 6. Mail notes

For mail delivery to work well, also configure:

- Reverse DNS (PTR) for the server IP to `mail.sudoinnovation.tech`
- SPF, DKIM, and DMARC records
- Port `25` open if you want to receive mail from external servers

Without PTR and DKIM, inbox placement will be poor.

## 7. Docker Secrets Setup (Production)

For production deployments, use Docker secrets to store sensitive values instead of `.env` files.

### 7.1 Generate production secrets

Create a `secrets/` directory with real (not example) values:

```bash
mkdir -p secrets

# Generate strong random secrets (use any secure method)
# Example using openssl:
openssl rand -base64 32 > secrets/JWT_SECRET
openssl rand -base64 32 > secrets/JWT_REFRESH_SECRET
openssl rand -base64 32 > secrets/ENCRYPTION_KEY

# Set database password (replace with your actual password)
echo "your-strong-db-password" > secrets/POSTGRES_PASSWORD

# Set database URL (use pgbouncer inside docker-compose)
echo "postgresql+asyncpg://nexudo:your-strong-db-password@pgbouncer:6432/nexudo_mail" > secrets/DATABASE_URL

# Set Redis URL (internal to compose)
echo "redis://redis:6379/0" > secrets/REDIS_URL

# Set file permissions to read-only by owner
chmod 400 secrets/*
```

### 7.2 Start with Docker secrets

Compose will automatically read secret files and mount them into containers at `/run/secrets/<NAME>`. The backend config automatically loads secrets from there.

```bash
# Make sure .env is NOT used for production secrets
# Only use .env for non-secret config (DOMAIN, SMTP_HOSTNAME, etc.)
docker compose up -d --build
```

The backend startup checks will validate that all required secrets are present and meet minimum length requirements. If startup fails, check docker compose logs:

```bash
docker compose logs backend
```

### 7.3 Never commit secrets to VCS

The `.gitignore` excludes `secrets/` and `.env*` files. Ensure secrets are never committed:

```bash
# Verify secrets are not in Git
git ls-files | grep -E '^secrets/|^\.env' || echo "Good: no secret files in Git"
```

## 8. Initial Admin Provisioning

### 8.1 Development mode

If `ENVIRONMENT=development` (default), the backend auto-creates a super-admin on first run:

```bash
export ENVIRONMENT=development
docker compose up -d --build
docker compose logs backend | grep -i "admin"
```

The generated credentials are written to `/tmp/initial_super_admin.txt` inside the backend container. Retrieve them:

```bash
docker compose exec backend cat /tmp/initial_super_admin.txt
```

### 8.2 Production mode

For production (`ENVIRONMENT=production`), the auto-create feature is disabled. You must:

1. Run database migrations to ensure the `users` table exists.
2. Manually insert a super-admin via a one-time admin-init endpoint (planned) or directly via SQL:

```bash
# Connect to postgres inside compose
docker compose exec postgres psql -U nexudo -d nexudo_mail -c \
  "INSERT INTO users (email, password_hash, role, created_at, updated_at) \
   VALUES ('admin@sudoinnovation.tech', '<bcrypt_hash>', 'SUPER_ADMIN', NOW(), NOW());"
```

Alternatively, implement a secure one-time admin-init HTTP endpoint that requires a bootstrap token.

## 9. SMTP API Key Integration

The backend provides API endpoints to create and list SMTP credentials:

```bash
# Create an SMTP API key (authenticated as super-admin)
curl -X POST https://api.sudoinnovation.tech/api/v1/smtp/keys \
  -H "Authorization: Bearer <admin_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"domain_id": 1, "name": "My SMTP Key"}'

# Response: { "key": "nexudo_sk_...", "prefix": "nexudo_sk_xxxx" }
```

For mailserver integration, SMTP credentials are stored in the database and should be queried from there (not hard-coded). The docker-mailserver container can be configured to use a custom auth backend or relay configuration.

## 10. Pre-Deployment Checklist

Before going live, verify:

### Infrastructure & DNS

- [ ] Server has open ports: 80, 443, 25, 587, 993
- [ ] DNS A records point to server IP (ROOT_DOMAIN, API_DOMAIN, MAIL_DOMAIN)
- [ ] MX record points to MAIL_DOMAIN
- [ ] SPF record configured (`v=spf1 mx -all`)
- [ ] DKIM keys generated and added to DNS
- [ ] DMARC policy configured
- [ ] Reverse DNS (PTR) set to mail.sudoinnovation.tech

### Secrets & Credentials

- [ ] All Docker secrets created and stored securely (not in repo)
- [ ] JWT_SECRET, JWT_REFRESH_SECRET, ENCRYPTION_KEY are random and ≥32 chars
- [ ] POSTGRES_PASSWORD is strong and unique
- [ ] .env file contains only non-secret config (domains, ports, app names)
- [ ] No hard-coded passwords in docker-compose.yml or code
- [ ] TRAEFIK_ACME_EMAIL set (used for Let's Encrypt)

### Application Setup

- [ ] ENVIRONMENT set to "production"
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
