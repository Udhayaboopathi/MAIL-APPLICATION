"use client";

import { useState } from "react";

import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";

export default function DomainAdminPage() {
  const [domain, setDomain] = useState("nexudo.dev");
  return (
    <main className="min-h-screen bg-slate-950 p-6 text-text">
      <section className="rounded-[32px] border border-white/10 bg-white/5 p-6">
        <div className="font-display text-3xl font-semibold">Domain Admin</div>
        <p className="mt-2 text-sm text-muted">
          Manage mailbox quotas, DNS verification, and domain backups.
        </p>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <Input
            value={domain}
            onChange={(event) => setDomain(event.target.value)}
          />
          <Button>Verify DNS</Button>
        </div>
      </section>
    </main>
  );
}
