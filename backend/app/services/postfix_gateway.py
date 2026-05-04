from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


class PostfixGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    def deliver(self, *, sender: str, recipients: list[str], subject: str, text: str | None, html: str | None) -> tuple[bool, str]:
        message = EmailMessage()
        message["From"] = sender
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        if html and text:
            message.set_content(text)
            message.add_alternative(html, subtype="html")
        elif html:
            message.add_alternative(html, subtype="html")
        else:
            message.set_content(text or "")

        with smtplib.SMTP(self.settings.smtp_hostname, self.settings.smtp_port, timeout=30) as client:
            client.ehlo()
            if self.settings.smtp_port == 587:
                client.starttls()
                client.ehlo()
            # SMTP credentials should NOT come from environment. The system will
            # fetch SMTP credentials (if required) from the DB (mailbox or api key) at call site.
            if getattr(self.settings, "smtp_username", None) and getattr(self.settings, "smtp_password", None):
                client.login(self.settings.smtp_username, self.settings.smtp_password)
            response = client.send_message(message)
        return True, str(response)
