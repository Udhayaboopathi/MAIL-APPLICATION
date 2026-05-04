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

## Server and DNS setup

See [docs/server-and-dns.md](docs/server-and-dns.md) for the production VPS, firewall, Traefik, and DNS record setup.
