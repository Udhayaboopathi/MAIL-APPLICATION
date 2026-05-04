import { LogTable } from "../../../components/log-table";
import { StatCard } from "../../../components/stat-card";

const logs = [
  {
    id: "log_1",
    apiKey: "nexudo_sk_84f1",
    recipient: "alice@sudoinnovation.tech",
    status: "delivered",
    latency: "82 ms",
  },
  {
    id: "log_2",
    apiKey: "nexudo_sk_2ad9",
    recipient: "ops@sudoinnovation.tech",
    status: "queued",
    latency: "14 ms",
  },
  {
    id: "log_3",
    apiKey: "nexudo_sk_7b31",
    recipient: "team@client.com",
    status: "bounced",
    latency: "191 ms",
  },
];

export default function DashboardPage() {
  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="hero">
        <div className="toolbar">
          <div>
            <div className="pill">Realtime operations</div>
            <h1
              style={{
                fontFamily: "var(--font-display)",
                fontSize: "clamp(2rem, 4vw, 3.5rem)",
                margin: "10px 0",
              }}
            >
              Command center
            </h1>
            <div className="muted">
              Monitor domains, mailboxes, SMTP traffic, and delivery health from
              a single role-aware control plane.
            </div>
          </div>
          <button className="button">Add Domain</button>
        </div>
        <div className="grid three">
          <StatCard label="Domains" value="18" detail="4 verified this week" />
          <StatCard
            label="Mailboxes"
            value="2,481"
            detail="92% active accounts"
          />
          <StatCard
            label="SMTP throughput"
            value="1.2M"
            detail="messages processed today"
          />
        </div>
      </section>
      <div className="grid two">
        <section className="panel stat">
          <div className="muted">Live metrics</div>
          <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
            <div className="toolbar">
              <span>Sent</span>
              <strong>124,221</strong>
            </div>
            <div className="toolbar">
              <span>Delivered</span>
              <strong>121,905</strong>
            </div>
            <div className="toolbar">
              <span>Bounced</span>
              <strong>1,932</strong>
            </div>
            <div className="toolbar">
              <span>Queued</span>
              <strong>384</strong>
            </div>
          </div>
        </section>
        <section className="panel stat">
          <div className="muted">Activity feed</div>
          <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
            <div className="toolbar">
              <span>Cloudflare DNS sync</span>
              <strong>Done</strong>
            </div>
            <div className="toolbar">
              <span>DKIM key rotation</span>
              <strong>Scheduled</strong>
            </div>
            <div className="toolbar">
              <span>Backup export</span>
              <strong>Completed</strong>
            </div>
          </div>
        </section>
      </div>
      <LogTable rows={logs} />
    </div>
  );
}
