from __future__ import annotations

from dataclasses import dataclass

from app.services.maildir import MaildirStore


@dataclass(slots=True)
class IMAPHandler:
    maildir: MaildirStore

    def list_messages(self, domain: str, local_part: str) -> list[str]:
        return self.maildir.list_keys(domain, local_part)

    def search_messages(self, domain: str, local_part: str, query: str) -> list[dict]:
        return self.maildir.search_subject(domain, local_part, query)
