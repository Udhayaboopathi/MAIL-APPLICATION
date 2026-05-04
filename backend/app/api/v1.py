from __future__ import annotations

from email.parser import BytesParser
from email.policy import default as email_default_policy
from email.utils import parseaddr

import hashlib
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_value, generate_api_key, hash_password
from app.db.session import get_db
from app.deps import RequestContext, get_current_api_key, get_current_user, get_request_context, require_role
from app.models import ApiKey, AuditLog, Domain, EmailMessage, Mailbox, Tenant, User, Webhook
from app.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResult,
    ApiKeyOut,
    BackupRequest,
    BackupResult,
    DomainCreate,
    DomainOut,
    InboundEmailResult,
    LoginRequest,
    MailboxCreate,
    MailboxOut,
    MetricsOut,
    EmailDeleteRequest,
    EmailMoveRequest,
    EmailQuery,
    EmailScheduleRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PlatformStatsOut,
    RefreshRequest,
    SendEmailRequest,
    SendEmailResponse,
    TotpSetupOut,
    TotpVerifyRequest,
    TenantCreate,
    TenantOut,
    TokenPair,
    UserOut,
    WebhookCreate,
)
from app.services.auth import authenticate_user, logout_session, refresh_tokens, request_password_reset, reset_password, setup_totp, verify_totp
from app.services.backup import BackupService
from app.services.cloudflare import CloudflareDNSService, build_mail_dns_records
from app.services.maildir import MaildirStore
from app.services.metrics import increment_metric
from app.services.redis import get_json
from app.services.smtp import send_email
from app.services.webhooks import dispatch_webhook


router = APIRouter()


@router.post("/auth/login", response_model=TokenPair)
async def login(payload: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    context = await get_request_context(request)
    return await authenticate_user(db, payload, context)


@router.post("/auth/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(db, payload)


@router.post("/auth/logout")
async def logout(payload: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await logout_session(db, payload.refresh_token)
    return {"status": "logged_out"}


@router.post("/auth/password-reset/request")
async def password_reset_request(payload: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    token = await request_password_reset(db, payload.email)
    return {"status": "accepted", "reset_token": token}


@router.post("/auth/password-reset/confirm")
async def password_reset_confirm(payload: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    await reset_password(db, payload.token, payload.new_password)
    return {"status": "password_updated"}


@router.post("/auth/totp/setup", response_model=TotpSetupOut)
async def totp_setup(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await setup_totp(db, current_user)


@router.post("/auth/totp/verify")
async def totp_verify(payload: TotpVerifyRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    verified = await verify_totp(db, current_user, payload.code)
    return {"verified": verified}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/tenants", response_model=TenantOut)
async def create_tenant(payload: TenantCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN"))):
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    db.add(AuditLog(actor_user_id=current_user.id, tenant_id=None, action="tenant.create", metadata=payload.model_dump()))
    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("/tenants", response_model=list[TenantOut])
async def list_tenants(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN"))):
    result = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return result.scalars().all()


@router.post("/domains", response_model=DomainOut)
async def create_domain(payload: DomainCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN", "DOMAIN_ADMIN"))):
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == payload.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    dkim_public_key = f"v=DKIM1; k=rsa; p={hashlib.sha256(payload.name.encode('utf-8')).hexdigest()}"
    domain = Domain(
        tenant_id=payload.tenant_id,
        name=payload.name,
        storage_quota_bytes=payload.storage_quota_bytes,
        cloudflare_zone_id=payload.cloudflare_zone_id,
        cloudflare_token_encrypted=encrypt_value(payload.cloudflare_token) if payload.cloudflare_token else None,
        dkim_public_key=dkim_public_key,
        dkim_private_key_encrypted=encrypt_value(f"dkim-private-{payload.name}"),
    )
    db.add(domain)
    if payload.use_cloudflare and payload.cloudflare_token and payload.cloudflare_zone_id:
        cf = CloudflareDNSService(payload.cloudflare_token, payload.cloudflare_zone_id)
        for record in build_mail_dns_records(payload.name, dkim_public_key, "mail.sudoinnovation.tech"):
            await cf.create_or_update_record(type_=record["type"], name=record["name"], content=record["content"], proxied=record.get("proxied", False))
    await db.commit()
    await db.refresh(domain)
    return domain


@router.get("/domains", response_model=list[DomainOut])
async def list_domains(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Domain)
    if current_user.role != "SUPER_ADMIN":
        stmt = stmt.where(Domain.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt.order_by(Domain.created_at.desc()))
    return result.scalars().all()


@router.post("/mailboxes", response_model=MailboxOut)
async def create_mailbox(payload: MailboxCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN", "DOMAIN_ADMIN"))):
    domain_result = await db.execute(select(Domain).where(Domain.id == payload.domain_id))
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")
    email_address = f"{payload.local_part}@{domain.name}"
    mailbox = Mailbox(
        tenant_id=payload.tenant_id,
        domain_id=payload.domain_id,
        local_part=payload.local_part,
        email_address=email_address,
        password_hash=hash_password(payload.password),
        quota_bytes=payload.quota_bytes,
    )
    db.add(mailbox)
    await db.commit()
    await db.refresh(mailbox)
    return mailbox


@router.get("/mailboxes", response_model=list[MailboxOut])
async def list_mailboxes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Mailbox)
    if current_user.role != "SUPER_ADMIN":
        stmt = stmt.where(Mailbox.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt.order_by(Mailbox.created_at.desc()))
    return result.scalars().all()


@router.post("/api-keys", response_model=ApiKeyCreateResult)
async def create_api_key(payload: ApiKeyCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN", "DOMAIN_ADMIN"))):
    secret, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        tenant_id=payload.tenant_id,
        name=payload.name,
        key_prefix=prefix,
        key_hash=key_hash,
        permissions=payload.permissions,
        allowed_domains=payload.allowed_domains,
        sandbox_mode=payload.sandbox_mode,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyCreateResult(**ApiKeyOut.model_validate(api_key).model_dump(), secret=secret)


@router.post("/smtp/keys", response_model=ApiKeyCreateResult)
async def create_smtp_api_key(payload: ApiKeyCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN", "DOMAIN_ADMIN"))):
    """Create an API key intended for SMTP usage. The secret is returned only once."""
    secret, prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        tenant_id=payload.tenant_id,
        name=payload.name,
        key_prefix=prefix,
        key_hash=key_hash,
        permissions=payload.permissions,
        allowed_domains=payload.allowed_domains,
        sandbox_mode=payload.sandbox_mode,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyCreateResult(**ApiKeyOut.model_validate(api_key).model_dump(), secret=secret)


@router.get("/smtp/keys", response_model=list[ApiKeyOut])
async def list_smtp_api_keys(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ApiKey)
    if current_user.role != "SUPER_ADMIN":
        stmt = stmt.where(ApiKey.tenant_id == current_user.tenant_id)
    result = await db.execute(stmt.order_by(ApiKey.created_at.desc()))
    return result.scalars().all()


@router.get("/smtp/credentials")
async def smtp_credentials(current_user: User = Depends(get_current_user)):
    return {
        "smtp_host": "mail.sudoinnovation.tech",
        "smtp_port": 587,
        "smtp_user": "apikey",
        "smtp_password_example": "nexudo_sk_xxx",
        "allowed_auth": ["mailbox-password", "api-key"],
    }


@router.post("/send-email", response_model=SendEmailResponse)
async def send_email_endpoint(payload: SendEmailRequest, api_key: ApiKey = Depends(get_current_api_key), db: AsyncSession = Depends(get_db)):
    return await send_email(db, api_key, payload)


@router.post("/send", response_model=SendEmailResponse)
async def send_external(payload: SendEmailRequest, api_key: ApiKey = Depends(get_current_api_key), db: AsyncSession = Depends(get_db)):
    return await send_email(db, api_key, payload)


@router.post("/send-template", response_model=SendEmailResponse)
async def send_template(payload: SendEmailRequest, api_key: ApiKey = Depends(get_current_api_key), db: AsyncSession = Depends(get_db)):
    return await send_email(db, api_key, payload)


@router.post("/webhooks", response_model=dict)
async def create_webhook(payload: WebhookCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN", "DOMAIN_ADMIN"))):
    webhook = Webhook(**payload.model_dump())
    db.add(webhook)
    await db.commit()
    return {"id": str(webhook.id), "status": "created"}


@router.get("/metrics", response_model=MetricsOut)
async def metrics(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    raw = await get_json(f"metrics:{current_user.tenant_id}") or {}
    return MetricsOut(
        sent=int(raw.get("sent", 0)),
        delivered=int(raw.get("delivered", 0)),
        bounced=int(raw.get("bounced", 0)),
        failed=int(raw.get("failed", 0)),
        queued=int(raw.get("queued", 0)),
    )


@router.post("/backup", response_model=BackupResult)
async def backup(payload: BackupRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = BackupService()
    tenant_id = str(payload.tenant_id or current_user.tenant_id)
    file_path, _ = await service.export_tenant(db, tenant_id)
    return BackupResult(job_id=__import__("uuid").uuid4(), status="completed", storage_key=file_path)


@router.get("/mail/emails")
async def list_emails(payload: EmailQuery = Depends(), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(EmailMessage).where(EmailMessage.tenant_id == current_user.tenant_id)
    if payload.folder:
        stmt = stmt.where(EmailMessage.delivery_status == payload.folder)
    if payload.search:
        term = f"%{payload.search.lower()}%"
        stmt = stmt.where(
            func.lower(EmailMessage.subject).like(term)
            | func.lower(EmailMessage.sender).like(term)
            | func.lower(EmailMessage.snippet).like(term)
        )
    if payload.unread_only:
        stmt = stmt.where(EmailMessage.is_read.is_(False))
    result = await db.execute(stmt.order_by(EmailMessage.created_at.desc()).offset(payload.offset).limit(payload.limit))
    return [
        {
            "id": str(email.id),
            "subject": email.subject,
            "sender": email.sender,
            "recipients": email.recipients,
            "delivery_status": email.delivery_status,
            "is_read": email.is_read,
            "thread_id": str(email.thread_id) if email.thread_id else None,
            "created_at": email.created_at,
        }
        for email in result.scalars().all()
    ]


@router.post("/mail/emails/move")
async def move_email(payload: EmailMoveRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(EmailMessage).where(EmailMessage.id == payload.email_id, EmailMessage.tenant_id == current_user.tenant_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    email.delivery_status = payload.folder
    await db.commit()
    return {"status": "moved"}


@router.delete("/mail/emails")
async def delete_email(payload: EmailDeleteRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(EmailMessage).where(EmailMessage.id == payload.email_id, EmailMessage.tenant_id == current_user.tenant_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")
    await db.delete(email)
    await db.commit()
    return {"status": "deleted"}


@router.post("/mail/emails/schedule")
async def schedule_email(payload: EmailScheduleRequest, api_key: ApiKey = Depends(get_current_api_key), db: AsyncSession = Depends(get_db)):
    mailbox_result = await db.execute(select(Mailbox).where(Mailbox.tenant_id == payload.tenant_id, Mailbox.email_address == payload.from_email))
    mailbox = mailbox_result.scalar_one_or_none()
    if not mailbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mailbox not found for sender")
    email = EmailMessage(
        tenant_id=payload.tenant_id,
        mailbox_id=mailbox.id,
        sender=payload.from_email,
        recipients=list(payload.to),
        subject=payload.subject,
        direction="outbound",
        delivery_status="scheduled",
        scheduled_for=payload.send_at,
        metadata={"variables": payload.variables},
    )
    db.add(email)
    await db.commit()
    from app.workers.tasks import scheduled_emails

    scheduled_emails.apply_async((str(email.id),), eta=payload.send_at)
    return {"status": "scheduled", "email_id": str(email.id)}


@router.get("/super-admin/stats", response_model=PlatformStatsOut)
async def platform_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(require_role("SUPER_ADMIN"))):
    tenant_count = (await db.execute(select(func.count()).select_from(Tenant))).scalar_one()
    domain_count = (await db.execute(select(func.count()).select_from(Domain))).scalar_one()
    mailbox_count = (await db.execute(select(func.count()).select_from(Mailbox))).scalar_one()
    message_count = (await db.execute(select(func.count()).select_from(EmailMessage))).scalar_one()
    queued_count = (await db.execute(select(func.count()).select_from(EmailMessage).where(EmailMessage.delivery_status == "queued"))).scalar_one()
    delivered_count = (await db.execute(select(func.count()).select_from(EmailMessage).where(EmailMessage.delivery_status == "delivered"))).scalar_one()
    return PlatformStatsOut(
        tenants=tenant_count,
        domains=domain_count,
        mailboxes=mailbox_count,
        messages=message_count,
        queued=queued_count,
        delivered=delivered_count,
    )


@router.post("/inbound-email", response_model=InboundEmailResult)
async def inbound_email(payload: dict, db: AsyncSession = Depends(get_db)):
    raw_message = payload.get("raw_message", "")
    if not raw_message:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="raw_message is required")

    message = BytesParser(policy=email_default_policy).parsebytes(raw_message.encode("utf-8"))
    recipient = parseaddr(message.get("to", ""))[1] or message.get("to", "")
    sender = parseaddr(message.get("from", ""))[1] or message.get("from", "")
    subject = message.get("subject")
    recipient_domain = recipient.split("@")[-1].lower() if "@" in recipient else None
    if not recipient_domain:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Recipient missing")

    domain_result = await db.execute(select(Domain).where(Domain.name == recipient_domain))
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Domain not found")

    mailbox_result = await db.execute(select(Mailbox).where(Mailbox.email_address == recipient))
    mailbox = mailbox_result.scalar_one_or_none()
    from app.models import InboundEmail

    inbound = InboundEmail(
        tenant_id=domain.tenant_id,
        domain_id=domain.id,
        mailbox_id=mailbox.id if mailbox else None,
        message_id=message.get("message-id"),
        sender=sender,
        recipient=recipient,
        subject=subject,
        headers={key: value for key, value in message.items()},
        metadata={"size": len(raw_message), "attachments": sum(1 for part in message.walk() if part.get_content_disposition() == "attachment")},
    )
    db.add(inbound)
    maildir = MaildirStore()
    local_part = recipient.split("@", 1)[0]
    maildir.store_raw(domain.name, local_part, raw_message.encode("utf-8"))
    maildir.extract_attachments(raw_message.encode("utf-8"), f"/var/mail/{domain.name}/{local_part}/attachments")
    await db.commit()
    await dispatch_webhook(
        url=payload.get("webhook_url", ""),
        secret=payload.get("webhook_secret", ""),
        payload={"event": "inbound_email", "recipient": recipient, "sender": sender, "subject": subject, "tenant_id": str(domain.tenant_id)},
    ) if payload.get("webhook_url") and payload.get("webhook_secret") else None
    return InboundEmailResult(message_id=inbound.message_id, status="processed", recipient=recipient, sender=sender)
