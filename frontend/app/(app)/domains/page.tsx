export default function DomainsPage() {
  return (
    <section className="hero">
      <div className="toolbar">
        <div>
          <div className="pill">Domain management</div>
          <h1
            style={{ fontFamily: "var(--font-display)", margin: "12px 0 6px" }}
          >
            Domains
          </h1>
          <div className="muted">
            Add domains, automate Cloudflare DNS, and manage DKIM and quotas.
          </div>
        </div>
        <button className="button">Add Domain</button>
      </div>
      <div className="grid two">
        <div className="panel stat">
          <strong>nexudo.dev</strong>
          <p className="muted">Verified, DKIM enabled, 250 GB quota.</p>
        </div>
        <div className="panel stat">
          <strong>mail.nexudo.dev</strong>
          <p className="muted">Internal SMTP and IMAP endpoint.</p>
        </div>
      </div>
    </section>
  );
}
