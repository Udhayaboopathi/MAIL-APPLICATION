from __future__ import annotations

import httpx


class CloudflareDNSService:
    def __init__(self, token: str, zone_id: str) -> None:
        self.token = token
        self.zone_id = zone_id

    async def create_or_update_record(self, *, type_: str, name: str, content: str, ttl: int = 1, proxied: bool = False) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records",
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
                json={"type": type_, "name": name, "content": content, "ttl": ttl, "proxied": proxied},
            )
            response.raise_for_status()
            return response.json()


def build_mail_dns_records(domain: str, dkim_public_key: str, mail_host: str) -> list[dict]:
    return [
        {"type": "MX", "name": domain, "content": mail_host, "priority": 10},
        {"type": "TXT", "name": domain, "content": "v=spf1 mx include:_spf.sudoinnovation.tech -all"},
        {"type": "TXT", "name": f"default._domainkey.{domain}", "content": dkim_public_key},
        {"type": "TXT", "name": f"_dmarc.{domain}", "content": "v=DMARC1; p=quarantine; rua=mailto:postmaster@sudoinnovation.tech"},
    ]
