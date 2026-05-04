from __future__ import annotations

import mailbox
import os
import shutil
import uuid
from email.message import Message
from email.parser import BytesParser
from email.policy import default as default_policy
from pathlib import Path


class MaildirStore:
    def __init__(self, root: str = "/var/mail") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def mailbox_path(self, domain: str, local_part: str) -> Path:
        return self.root / domain / local_part

    def ensure_maildir(self, domain: str, local_part: str) -> mailbox.Maildir:
        path = self.mailbox_path(domain, local_part)
        path.mkdir(parents=True, exist_ok=True)
        return mailbox.Maildir(str(path), create=True)

    def store_raw(self, domain: str, local_part: str, raw_message: bytes) -> str:
        maildir = self.ensure_maildir(domain, local_part)
        key = maildir.add(raw_message)
        maildir.flush()
        return str(key)

    def store_sent_copy(self, domain: str, local_part: str, raw_message: bytes) -> str:
        return self.store_raw(domain, local_part, raw_message)

    def list_keys(self, domain: str, local_part: str) -> list[str]:
        maildir = self.ensure_maildir(domain, local_part)
        return list(maildir.keys())

    def search_subject(self, domain: str, local_part: str, query: str) -> list[dict]:
        maildir = self.ensure_maildir(domain, local_part)
        matches: list[dict] = []
        for key, message in maildir.items():
            parsed = BytesParser(policy=default_policy).parsebytes(message.as_bytes())
            subject = parsed.get("subject", "")
            if query.lower() in subject.lower():
                matches.append({"key": key, "subject": subject, "from": parsed.get("from"), "to": parsed.get("to")})
        return matches

    def extract_attachments(self, raw_message: bytes, target_dir: str) -> list[str]:
        message = BytesParser(policy=default_policy).parsebytes(raw_message)
        output_dir = Path(target_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        saved: list[str] = []
        for part in message.walk():
            if part.get_content_disposition() != "attachment":
                continue
            filename = part.get_filename() or f"attachment-{uuid.uuid4()}"
            path = output_dir / filename
            with path.open("wb") as handle:
                handle.write(part.get_payload(decode=True) or b"")
            saved.append(str(path))
        return saved
