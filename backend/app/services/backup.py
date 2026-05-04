from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import inspect, select
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BackupJob, Domain, Mailbox, Tenant


class BackupService:
    def __init__(self, backup_root: str = "/tmp/nexudo-backups") -> None:
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

    async def export_tenant(self, db: AsyncSession, tenant_id: str) -> tuple[str, dict]:
        tables = {
            "tenant": (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none(),
            "domains": (await db.execute(select(Domain).where(Domain.tenant_id == tenant_id))).scalars().all(),
            "mailboxes": (await db.execute(select(Mailbox).where(Mailbox.tenant_id == tenant_id))).scalars().all(),
        }
        payload = {name: self._serialize(value) for name, value in tables.items()}
        file_path = self.backup_root / f"tenant-{tenant_id}.json"
        file_path.write_text(json.dumps(payload, default=str, indent=2), encoding="utf-8")
        return str(file_path), payload

    def _serialize(self, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, list):
            return [self._serialize(item) for item in value]
        mapper = inspect(value)
        return {column.key: getattr(value, column.key) for column in mapper.mapper.column_attrs}
