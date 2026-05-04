from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import ApiKey, Domain, EmailEvent, Mailbox, SmtpLog
from app.schemas import SendEmailRequest, SendEmailResponse
from app.services.redis import incr_rate_limit, publish_event, redis_client
from app.services.webhooks import dispatch_webhook


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(slots=True)
class EmailValidationResult:
    accepted: bool
    reason: str | None = None


def validate_email_address(address: str) -> bool:
    return bool(EMAIL_REGEX.match(address))


async def rate_limit_send(tenant_id: str, api_key_id: str, burst: int = 60) -> None:
    count = await incr_rate_limit(f"smtp:rate:{tenant_id}:{api_key_id}", 60)
    if count > burst:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


async def send_email(db: AsyncSession, api_key: ApiKey, request: SendEmailRequest) -> SendEmailResponse:
    if not validate_email_address(request.from_email) or any(not validate_email_address(addr) for addr in request.to):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid email address")
    if api_key.sandbox_mode or request.sandbox:
        recipient = request.to[0]
        await publish_event("smtp:events", {"event": "sandbox-capture", "to": recipient, "from": request.from_email})
        return SendEmailResponse(message_id=str(uuid.uuid4()), status="sandbox")

    allowed_domains = set(api_key.allowed_domains or [])
    sender_domain = request.from_email.split("@")[-1].lower()
    if allowed_domains and sender_domain not in allowed_domains:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sender domain not allowed")

    await rate_limit_send(str(request.tenant_id), str(api_key.id))

    log = SmtpLog(
        tenant_id=request.tenant_id,
        api_key_id=api_key.id,
        sender=request.from_email,
        recipient=request.to[0],
        subject=request.subject,
        status="queued",
        latency_ms=0,
        provider_response="queued for postfix delivery",
        message_id=str(uuid.uuid4()),
    )
    db.add(log)
    db.add(EmailEvent(
        tenant_id=request.tenant_id,
        smtp_log_id=log.id,
        event_type="queued",
        metadata={"priority": request.priority, "template_id": request.template_id},
    ))
    await db.commit()
    await publish_event("smtp:queue", {"message_id": log.message_id, "tenant_id": str(request.tenant_id), "recipient": request.to[0]})
    if not api_key.sandbox_mode:
        from app.workers.tasks import send_email_task

        send_email_task.delay(
            {
                "message_id": log.message_id,
                "sender": request.from_email,
                "recipients": list(request.to),
                "subject": request.subject,
                "text": request.text,
                "html": request.html,
                "priority": request.priority,
            }
        )
    return SendEmailResponse(message_id=log.message_id or str(uuid.uuid4()), status="queued")


async def record_delivery_event(db: AsyncSession, tenant_id: str, message_id: str, event_type: str, metadata: dict) -> None:
    result = await db.execute(__import__("sqlalchemy").select(SmtpLog).where(SmtpLog.message_id == message_id))
    log = result.scalar_one_or_none()
    if not log:
        return
    log.status = event_type
    db.add(EmailEvent(tenant_id=log.tenant_id, smtp_log_id=log.id, event_type=event_type, metadata=metadata))
    await db.commit()


async def emit_webhook_for_event(db: AsyncSession, tenant_id: str, event_type: str, payload: dict) -> None:
    from sqlalchemy import select
    from app.models import Webhook

    result = await db.execute(select(Webhook).where(Webhook.tenant_id == tenant_id, Webhook.is_active.is_(True)))
    for webhook in result.scalars().all():
        if webhook.events and event_type not in webhook.events:
            continue
        await dispatch_webhook(webhook.url, webhook.secret, payload)
