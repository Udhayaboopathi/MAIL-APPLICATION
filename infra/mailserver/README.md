# Mailserver runtime config

This folder holds docker-mailserver runtime configuration mounted into the mail container.

## Notes

- Fail2Ban rules live in `config/fail2ban/jail.local`.
- Rspamd and DKIM configuration snippets live under `config/rspamd`.
- DKIM private keys are generated and encrypted by the control plane; they are not stored in `.env`.
