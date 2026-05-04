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
ROOT_DOMAIN=example.com
WEB_DOMAIN=example.com
API_DOMAIN=api.example.com
MAIL_DOMAIN=mail.example.com
SMTP_HOSTNAME=mail.example.com
TRAEFIK_ACME_EMAIL=admin@example.com
```

Other important values already used by the stack:

- `DATABASE_URL` points to `pgbouncer:6432`
- `REDIS_URL` points to `redis:6379`
- `NEXT_PUBLIC_API_BASE_URL` should point to the public API URL in production

## 3. DNS records

Create these DNS records for your domain.

| Type  | Name           | Value                                                       | Notes                              |
| ----- | -------------- | ----------------------------------------------------------- | ---------------------------------- |
| A     | `@`            | your server IPv4                                            | Frontend root domain               |
| A     | `api`          | your server IPv4                                            | Backend API                        |
| A     | `mail`         | your server IPv4                                            | Mail server                        |
| MX    | `@`            | `mail.example.com`                                          | Mail delivery                      |
| TXT   | `@`            | `v=spf1 mx ip4:YOUR_SERVER_IP -all`                         | Basic sender policy                |
| TXT   | `_dmarc`       | `v=DMARC1; p=quarantine; rua=mailto:postmaster@example.com` | DMARC policy                       |
| CNAME | `autoconfig`   | `mail.example.com`                                          | Optional mail client auto-config   |
| CNAME | `autodiscover` | `mail.example.com`                                          | Optional mail client auto-discover |

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
   - `https://example.com`
   - `https://api.example.com`

## 6. Mail notes

For mail delivery to work well, also configure:

- Reverse DNS (PTR) for the server IP to `mail.example.com`
- SPF, DKIM, and DMARC records
- Port `25` open if you want to receive mail from external servers

Without PTR and DKIM, inbox placement will be poor.
