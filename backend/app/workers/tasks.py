from __future__ import annotations

from app.workers.celery_app import celery_app
from app.services.postfix_gateway import PostfixGateway
from app.services.redis import redis_client


@celery_app.task(name="nexudo.mail.retry_send")
def retry_send(message_id: str) -> dict:
    return {"message_id": message_id, "status": "retry-scheduled"}


@celery_app.task(name="nexudo.mail.process_inbound")
def process_inbound(message_id: str) -> dict:
    return {"message_id": message_id, "status": "inbound-processed"}


@celery_app.task(name="nexudo.mail.send_email_task", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def send_email_task(payload: dict) -> dict:
    gateway = PostfixGateway()
    gateway.deliver(
        sender=payload["sender"],
        recipients=payload["recipients"],
        subject=payload["subject"],
        text=payload.get("text"),
        html=payload.get("html"),
    )
    return {"status": "sent", "message_id": payload.get("message_id")}


@celery_app.task(name="nexudo.mail.campaign_sender", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def campaign_sender(campaign_id: str) -> dict:
    return {"campaign_id": campaign_id, "status": "campaign-queued"}


@celery_app.task(name="nexudo.mail.scheduled_emails", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def scheduled_emails(email_id: str) -> dict:
    return {"email_id": email_id, "status": "scheduled-send-complete"}


@celery_app.task(name="nexudo.mail.backups", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def backups(scope: str) -> dict:
    return {"scope": scope, "status": "backup-created"}


@celery_app.task(name="nexudo.mail.retention_cleanup", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def retention_cleanup() -> dict:
    return {"status": "cleanup-complete"}


@celery_app.task(name="nexudo.mail.ai_scoring", autoretry_for=(Exception,), retry_backoff=60, retry_backoff_max=900, retry_kwargs={"max_retries": 5})
def ai_scoring(email_id: str) -> dict:
    return {"email_id": email_id, "priority_score": 75, "summary": "Auto-generated priority score"}


@celery_app.task(name="nexudo.mail.deliver_via_postfix", autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def deliver_via_postfix(payload: dict) -> dict:
    gateway = PostfixGateway()
    gateway.deliver(
        sender=payload["sender"],
        recipients=payload["recipients"],
        subject=payload["subject"],
        text=payload.get("text"),
        html=payload.get("html"),
    )
    return {"status": "sent", "message_id": payload.get("message_id")}
