export default function SmtpPage() {
  return (
    <section className="hero">
      <div className="toolbar">
        <div>
          <div className="pill">SMTP API</div>
          <h1
            style={{ fontFamily: "var(--font-display)", margin: "12px 0 6px" }}
          >
            Developer sending
          </h1>
          <div className="muted">
            Use mailbox credentials or API keys with sandbox mode, rate limits,
            and sender restrictions.
          </div>
        </div>
        <button className="button">Generate API Key</button>
      </div>
      <div className="grid two">
        <div className="panel stat">
          <strong>SMTP credentials</strong>
          <pre style={{ whiteSpace: "pre-wrap", color: "var(--muted)" }}>
            SMTP_HOST=mail.sudoinnovation.tech{`\n`}SMTP_PORT=587{`\n`}
            SMTP_USER=apikey
            {`\n`}SMTP_PASSWORD=nexudo_sk_xxx
          </pre>
        </div>
        <div className="panel stat">
          <strong>REST endpoints</strong>
          <pre style={{ whiteSpace: "pre-wrap", color: "var(--muted)" }}>
            POST /api/v1/send-email{`\n`}POST /api/v1/send-template
          </pre>
        </div>
      </div>
    </section>
  );
}
