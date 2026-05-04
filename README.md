# Nexudo Mail

Nexudo Mail is a multi-tenant email hosting and developer SMTP/API platform for `nexudo.dev`.

## Stack

- Mail layer: docker-mailserver, Postfix, Dovecot, Rspamd
- Backend: FastAPI, PostgreSQL, Redis, Celery
- Frontend: Next.js App Router
- Edge: Traefik

## Local start

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Open the frontend at `http://localhost:3000` and the API at `http://localhost:8000`.

## Documentation

- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Complete production deployment guide with secrets setup, DNS configuration, and security hardening.
- **[docs/server-and-dns.md](docs/server-and-dns.md)** — VPS prerequisites, Traefik configuration, DNS records, and troubleshooting.

## Security

This application is hardened for production:

- **Secrets management**: Uses Docker secrets for sensitive values (JWT tokens, encryption keys, DB passwords). See `secrets/` directory.
- **Environment-driven configuration**: All domains, ports, and service URLs are configurable via environment variables or secrets files.
- **Encrypted credentials**: SMTP API keys and Cloudflare tokens are encrypted using Fernet with a configurable encryption key.
- **Startup validation**: Production mode enforces minimum secret lengths and raises errors if any required secret is missing.
- **Admin provisioning**: In non-production environments, generates temporary super-admin credentials on first run. Production requires manual admin setup.
- **JWT authentication**: Access and refresh tokens with configurable expiration and secret keys.
- **TLS/HTTPS**: Traefik auto-issues Let's Encrypt certificates for all public domains.

See [docs/server-and-dns.md#12-security-reminders](docs/server-and-dns.md#12-security-reminders) for production security best practices.
