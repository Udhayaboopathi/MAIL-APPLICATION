from __future__ import annotations

from dataclasses import dataclass

from app.services.maildir import MaildirStore


@dataclass(slots=True)
class SMTPHandler:
    maildir: MaildirStore

    def accept_message(self, domain: str, local_part: str, raw_message: bytes) -> str:
        return self.maildir.store_raw(domain, local_part, raw_message)
