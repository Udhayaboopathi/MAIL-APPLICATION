# Production Deployment Guide

This guide walks you through deploying Nexudo Mail to a production VPS with Docker, Traefik, and Docker secrets.

## Quick Start

1. **Provision a VPS** (Ubuntu 22.04+, 2GB+ RAM, Docker + Docker Compose)
2. **Clone the repository** and configure secrets
3. **Set DNS records** pointing to your VPS IP
4. **Deploy** with `docker compose up -d --build`
5. **Verify** HTTPS, mail delivery, and health checks

## Step 1: Provision the Server

### Recommended specs

- **OS**: Ubuntu 22.04 LTS or similar
- **RAM**: 2GB+ (more for high volume)
- **CPU**: 1 vCPU+ (more for concurrent connections)
- **Storage**: 20GB+ (adjust for mail volume)
- **Networking**: Static IPv4, ports 80/443/25/587/993 open

### Install Docker & Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker (official method)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker compose version
```

## Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/Udhayaboopathi/MAIL-APPLICATION.git
cd MAIL-APPLICATION

# Create secrets directory
mkdir -p secrets

# Generate strong secrets using openssl
openssl rand -base64 32 > secrets/JWT_SECRET
openssl rand -base64 32 > secrets/JWT_REFRESH_SECRET
openssl rand -base64 32 > secrets/ENCRYPTION_KEY

# Set database credentials (use strong password)
echo "your-strong-db-password-here" > secrets/POSTGRES_PASSWORD
echo "postgresql+asyncpg://nexudo:your-strong-db-password-here@pgbouncer:6432/nexudo_mail" > secrets/DATABASE_URL
echo "redis://redis:6379/0" > secrets/REDIS_URL

# Secure secret files
chmod 400 secrets/*

# Configure .env (non-secret values only)
cat > .env << 'EOF'
# Database (secrets are in ./secrets/)
POSTGRES_DB=nexudo_mail
POSTGRES_USER=nexudo

# Domains - REPLACE with your actual domain
ROOT_DOMAIN=yourdomain.com
WEB_DOMAIN=yourdomain.com
API_DOMAIN=api.yourdomain.com
MAIL_DOMAIN=mail.yourdomain.com
SMTP_HOSTNAME=mail.yourdomain.com
SMTP_PORT=587

# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_APP_NAME=Nexudo Mail

# Traefik & Production
ENVIRONMENT=production
TRAEFIK_ACME_EMAIL=admin@yourdomain.com

# No secrets in .env! They come from ./secrets/
EOF
```

## Step 3: Configure DNS Records

Point your domain to the VPS IP. Example for `yourdomain.com`:

| Type | Name    | Value                  | TTL |
| ---- | ------- | ---------------------- | --- |
| A    | @       | YOUR_VPS_IP            | 300 |
| A    | api     | YOUR_VPS_IP            | 300 |
| A    | mail    | YOUR_VPS_IP            | 300 |
| MX   | @       | mail.yourdomain.com    | 300 |
| TXT  | @       | v=spf1 mx -all         | 300 |
| TXT  | \_dmarc | v=DMARC1; p=quarantine | 300 |

Wait 10-15 minutes for DNS to propagate:

```bash
nslookup api.yourdomain.com
```

## Step 4: Deploy

```bash
# Pull latest images and start services
docker compose up -d --build

# Check backend initialization
docker compose logs -f backend

# Once backend shows "Uvicorn running on 0.0.0.0:8000", move to next step
```

The startup will:

1. Validate all secrets are present and meet minimum length (production check)
2. Connect to and initialize the database
3. Start Redis, PgBouncer, Traefik, Celery worker/beat
4. Request Let's Encrypt certificates

## Step 5: Verify Deployment

### Check service health

```bash
# All services should be running
docker compose ps

# Backend health check
curl -I https://api.yourdomain.com/health

# Frontend
curl -I https://yourdomain.com

# Check Traefik dashboard (optional, restrict in firewall)
open https://yourdomain.com:8080
```

### Create initial admin

Connect to the database and insert a super-admin:

```bash
# Generate a bcrypt hash for a password (use an online tool or Python)
python3 -c "from passlib.context import CryptContext; pwd = CryptContext(schemes=['bcrypt']); print(pwd.hash('your-secure-password'))"

# Insert admin into database
docker compose exec postgres psql -U nexudo -d nexudo_mail << SQL
INSERT INTO users (email, password_hash, role, created_at, updated_at)
VALUES ('admin@yourdomain.com', '\$2b\$12\$...bcrypt_hash_here...', 'SUPER_ADMIN', NOW(), NOW());
SQL

# Verify
docker compose exec postgres psql -U nexudo -d nexudo_mail -c "SELECT email, role FROM users;"
```

### Test mail flow

```bash
# Create a test domain via API (after admin login)
curl -X POST https://api.yourdomain.com/api/v1/domains \
  -H "Authorization: Bearer <admin_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"domain": "test.yourdomain.com"}'

# Create a test mailbox
curl -X POST https://api.yourdomain.com/api/v1/mailboxes \
  -H "Authorization: Bearer <admin_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"domain_id": 1, "email": "info@test.yourdomain.com", "password": "test123"}'

# Check mailserver logs
docker compose logs mailserver | tail -20
```

## Step 6: Configure Mail Server (docker-mailserver)

The docker-mailserver is pre-configured but may need custom auth for SMTP API keys. Currently, mail can only be sent via the system mailboxes created in the database.

For advanced relay or custom SASL:

```bash
# Edit mailserver config (optional)
nano infra/mailserver/mailserver.env

# Restart mailserver
docker compose restart mailserver

# View mailserver setup logs
docker compose logs mailserver
```

## Backup & Recovery

### Enable automated backups

Backups run daily at 02:30 UTC. Create the backup passphrase secret:

```bash
# Generate passphrase
openssl rand -base64 16 > infra/backups/backup_passphrase
chmod 400 infra/backups/backup_passphrase

# Restart compose to mount the secret
docker compose down && docker compose up -d
```

### Manual backup

```bash
docker compose run --rm backup /backup/backup.sh
ls -lh infra/backups/
```

### Manual restore

```bash
# Find a backup file
ls infra/backups/

# Restore from backup (example)
docker compose run --rm backup /backup/restore.sh 20260501T023000Z overwrite
```

## Monitoring & Logs

### Real-time logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f mailserver
docker compose logs -f traefik
```

### Health checks

The `docker compose ps` output shows the health status of each service. Example:

```
CONTAINER                    STATUS
mail-applicatio-postgres     Up 5 minutes (healthy)
mail-applicatio-pgbouncer    Up 5 minutes (healthy)
mail-applicatio-redis        Up 5 minutes (healthy)
mail-applicatio-backend      Up 2 minutes (healthy)
mail-applicatio-frontend     Up 2 minutes
```

### Common issues

**Backend startup fails with "Startup secret checks failed"**

- Verify secrets exist and contain values: `ls -la secrets/`
- Check secret content: `cat secrets/JWT_SECRET | wc -c` (should be ≥32 bytes)

**Let's Encrypt certificate fails**

- Verify DNS resolves: `nslookup api.yourdomain.com`
- Check Traefik logs: `docker compose logs traefik | grep -i error`
- Ensure port 80 is open for HTTP-01 challenge

**Database connection refused**

- Check postgres health: `docker compose logs postgres | tail -20`
- Verify pgbouncer: `docker compose logs pgbouncer`
- Ensure POSTGRES_PASSWORD in secrets matches DATABASE_URL

## Security Hardening

### Firewall rules

```bash
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw allow 25/tcp  # SMTP (for receiving mail)
sudo ufw allow 587/tcp # SMTP submission
sudo ufw allow 993/tcp # IMAPS
sudo ufw enable
```

### Restrict admin dashboard

```bash
# Limit Traefik dashboard access (optional, via firewall)
sudo ufw allow from 203.0.113.1 to any port 8080
```

### SSL/TLS validation

```bash
# Verify certificate
curl -vI https://api.yourdomain.com 2>&1 | grep -i certificate

# Test SSL/TLS configuration
openssl s_client -connect api.yourdomain.com:443 -brief
```

### Secrets rotation (quarterly/yearly)

1. Generate new secrets
2. Update files in `./secrets/`
3. Restart services: `docker compose restart backend celery-worker celery-beat`
4. Invalidate existing JWT tokens (manual or automatic)

## Maintenance

### Update images

```bash
# Pull latest images
docker compose pull

# Rebuild and restart
docker compose up -d --build

# Check logs
docker compose logs -f
```

### Database migrations

```bash
# Alembic migrations (auto-run on startup, but can be manual)
docker compose run --rm backend alembic upgrade head
```

### Cleanup old data

```bash
# Remove old volumes (CAREFUL!)
docker volume prune
```

## Support & Troubleshooting

- **Logs**: Check `docker compose logs <service>` for errors
- **Health**: Run `docker compose ps` to see service status
- **Connectivity**: Use `docker compose exec <service> ping <host>` to test
- **Database**: Connect with `docker compose exec postgres psql -U nexudo -d nexudo_mail`

Refer to [docs/server-and-dns.md](./server-and-dns.md) for more infrastructure details.
