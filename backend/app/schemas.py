from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12)


class TotpSetupOut(BaseModel):
    secret: str
    provisioning_uri: str


class TotpVerifyRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class EmailQuery(BaseModel):
    folder: str | None = None
    search: str | None = None
    unread_only: bool = False
    limit: int = 50
    offset: int = 0


class EmailMoveRequest(BaseModel):
    email_id: uuid.UUID
    folder: str


class EmailDeleteRequest(BaseModel):
    email_id: uuid.UUID


class EmailScheduleRequest(BaseModel):
    tenant_id: uuid.UUID
    from_email: EmailStr
    to: list[EmailStr]
    subject: str
    text: str | None = None
    html: str | None = None
    send_at: datetime
    api_key: str | None = None
    variables: dict = Field(default_factory=dict)


class UserOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID | None
    email: EmailStr
    role: str
    full_name: str | None = None
    is_active: bool
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class TenantOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    storage_quota_bytes: int
    used_storage_bytes: int
    is_active: bool

    class Config:
        from_attributes = True


class TenantCreate(BaseModel):
    name: str
    slug: str
    storage_quota_bytes: int = 0


class DomainCreate(BaseModel):
    tenant_id: uuid.UUID
    name: str
    storage_quota_bytes: int = 0
    use_cloudflare: bool = False
    cloudflare_token: str | None = None
    cloudflare_zone_id: str | None = None


class DomainOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    storage_quota_bytes: int
    used_storage_bytes: int
    is_verified: bool
    is_enabled: bool
    dkim_selector: str
    dkim_public_key: str | None = None

    class Config:
        from_attributes = True


class MailboxCreate(BaseModel):
    tenant_id: uuid.UUID
    domain_id: uuid.UUID
    local_part: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=12)
    quota_bytes: int = 0


class MailboxOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    domain_id: uuid.UUID
    local_part: str
    email_address: EmailStr
    quota_bytes: int
    used_bytes: int
    is_enabled: bool

    class Config:
        from_attributes = True


class ApiKeyCreate(BaseModel):
    tenant_id: uuid.UUID
    name: str
    permissions: dict = Field(default_factory=dict)
    allowed_domains: list[str] = Field(default_factory=list)
    sandbox_mode: bool = False


class ApiKeyOut(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    key_prefix: str
    permissions: dict
    allowed_domains: list[str]
    sandbox_mode: bool
    is_enabled: bool

    class Config:
        from_attributes = True


class ApiKeyCreateResult(ApiKeyOut):
    secret: str


class SendEmailRequest(BaseModel):
    from_email: EmailStr
    to: list[EmailStr]
    subject: str
    text: str | None = None
    html: str | None = None
    tenant_id: uuid.UUID
    api_key: str | None = None
    template_id: str | None = None
    variables: dict = Field(default_factory=dict)
    priority: int = 5
    sandbox: bool = False


class SendEmailResponse(BaseModel):
    message_id: str
    status: str
    queued: bool = True


class WebhookCreate(BaseModel):
    tenant_id: uuid.UUID
    url: str
    secret: str
    events: list[str] = Field(default_factory=list)


class MetricsOut(BaseModel):
    sent: int
    delivered: int
    bounced: int
    failed: int
    queued: int


class BackupRequest(BaseModel):
    scope: str = Field(pattern="^(system|domain|mailbox)$")
    tenant_id: uuid.UUID | None = None
    mailbox_id: uuid.UUID | None = None
    mode: str = Field(default="export", pattern="^(export|import)$")
    strategy: str = Field(default="merge", pattern="^(merge|overwrite)$")


class BackupResult(BaseModel):
    job_id: uuid.UUID
    status: str
    storage_key: str | None = None


class PlatformStatsOut(BaseModel):
    tenants: int
    domains: int
    mailboxes: int
    messages: int
    queued: int
    delivered: int


class InboundEmailResult(BaseModel):
    message_id: str | None = None
    status: str
    recipient: str
    sender: str
