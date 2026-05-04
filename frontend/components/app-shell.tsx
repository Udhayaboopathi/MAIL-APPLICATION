"use client";

import {
  Archive,
  Inbox,
  Mail,
  Plus,
  Settings2,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";

import { useEmails } from "../hooks/use-emails";
import { useUiStore } from "../store/ui-store";
import { Button } from "./ui/button";
import { ComposeModal } from "./compose-modal";

const folders = [
  { id: "inbox", icon: Inbox, label: "Inbox" },
  { id: "sent", icon: Mail, label: "Sent" },
  { id: "archive", icon: Archive, label: "Archive" },
  { id: "spam", icon: Sparkles, label: "Priority Inbox" },
];

export function AppShell() {
  const selectedFolder = useUiStore((state) => state.selectedFolder);
  const setSelectedFolder = useUiStore((state) => state.setSelectedFolder);
  const { data: emails = [], isLoading } = useEmails();

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,rgba(65,200,170,0.14),transparent_24%),radial-gradient(circle_at_top_right,rgba(255,182,77,0.12),transparent_28%),linear-gradient(180deg,#06111f_0%,#07131f_100%)] text-text">
      <div className="grid min-h-screen grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-r border-white/10 bg-black/20 px-5 py-6 backdrop-blur-xl">
          <div className="font-display text-3xl font-semibold tracking-tight">
            Nexudo Mail
          </div>
          <p className="mt-2 text-sm text-muted">
            Self-hosted inbox and transactional email control plane.
          </p>
          <div className="mt-6">
            <ComposeModal />
          </div>
          <nav className="mt-8 space-y-2">
            {folders.map((folder) => {
              const Icon = folder.icon;
              const active = selectedFolder === folder.id;
              return (
                <button
                  key={folder.id}
                  onClick={() => setSelectedFolder(folder.id)}
                  className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left transition ${active ? "bg-white/10 text-white" : "text-muted hover:bg-white/5 hover:text-white"}`}
                >
                  <Icon size={18} />
                  <span>{folder.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="mt-8 space-y-2 rounded-3xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 text-sm text-muted">
              <Shield size={16} /> Super Admin
            </div>
            <div className="flex items-center gap-2 text-sm text-muted">
              <Users size={16} /> Domain Admin
            </div>
            <div className="flex items-center gap-2 text-sm text-muted">
              <Settings2 size={16} /> Mailbox User
            </div>
          </div>
        </aside>

        <main className="grid min-h-screen grid-cols-[minmax(320px,420px)_1fr] gap-0">
          <section className="border-r border-white/10 bg-black/10 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="font-display text-3xl font-semibold capitalize tracking-tight">
                  {selectedFolder}
                </h1>
                <p className="text-sm text-muted">
                  Realtime mail, threads, and delivery events.
                </p>
              </div>
              <Button className="rounded-full px-3 py-2">
                <Plus size={16} />
              </Button>
            </div>

            <div className="mt-5 space-y-3">
              {isLoading ? (
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5 text-muted">
                  Loading emails...
                </div>
              ) : (
                emails.map((email) => (
                  <article
                    key={email.id}
                    className="rounded-3xl border border-white/10 bg-white/5 p-4 transition hover:border-accent/40 hover:bg-white/10"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="font-semibold text-white">
                          {email.subject}
                        </div>
                        <div className="mt-1 text-sm text-muted">
                          {email.sender}
                        </div>
                      </div>
                      <span className="rounded-full border border-white/10 px-2 py-1 text-xs uppercase tracking-wide text-muted">
                        {email.delivery_status}
                      </span>
                    </div>
                  </article>
                ))
              )}
            </div>
          </section>

          <section className="p-6">
            <div className="rounded-[28px] border border-white/10 bg-[rgba(9,15,27,0.86)] p-6 shadow-glow">
              <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <div className="text-sm text-muted">Message reader</div>
                  <h2 className="font-display text-2xl font-semibold tracking-tight">
                    Select a thread to read mail
                  </h2>
                </div>
                <div className="text-sm text-muted">
                  Attachments, labels, and smart reply live here.
                </div>
              </div>
              <div className="mt-6 grid gap-4 md:grid-cols-2">
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                  <div className="text-sm text-muted">AI summary</div>
                  <p className="mt-2 text-sm leading-7 text-text/90">
                    Summaries are generated from the email body and thread
                    context for quick triage.
                  </p>
                </div>
                <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                  <div className="text-sm text-muted">Smart reply</div>
                  <p className="mt-2 text-sm leading-7 text-text/90">
                    The reply composer can suggest contextual replies and
                    priority scoring.
                  </p>
                </div>
              </div>
              <div className="mt-6 rounded-3xl border border-dashed border-white/15 bg-black/20 p-5 text-sm text-muted">
                Compose, schedule, or forward from the transaction-safe backend.
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
