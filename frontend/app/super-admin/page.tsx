"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "../../lib/api";

type Stats = {
  tenants: number;
  domains: number;
  mailboxes: number;
  messages: number;
  queued: number;
  delivered: number;
};

export default function SuperAdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    apiFetch<Stats>("/api/v1/super-admin/stats")
      .then(setStats)
      .catch(() =>
        setStats({
          tenants: 0,
          domains: 0,
          mailboxes: 0,
          messages: 0,
          queued: 0,
          delivered: 0,
        }),
      );
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-text">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-6">
        <div className="font-display text-3xl font-semibold">Super Admin</div>
        <p className="mt-2 text-sm text-muted">
          Platform-level domain provisioning, quotas, and stats.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {Object.entries(stats ?? {}).map(([label, value]) => (
            <div
              key={label}
              className="rounded-3xl border border-white/10 bg-black/20 p-4"
            >
              <div className="text-sm text-muted capitalize">{label}</div>
              <div className="mt-2 text-3xl font-semibold">
                {value as number}
              </div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
