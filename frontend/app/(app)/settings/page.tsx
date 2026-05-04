export default function SettingsPage() {
  return (
    <section className="hero">
      <div className="pill">Settings</div>
      <h1 style={{ fontFamily: "var(--font-display)", margin: "12px 0 6px" }}>
        Security and compliance
      </h1>
      <p className="muted">
        JWT sessions, login activity logs, Fail2Ban, TLS, and encrypted secrets
        live here in production.
      </p>
      <div className="grid two" style={{ marginTop: 24 }}>
        <div className="panel stat">
          <strong>Session tracking</strong>
          <p className="muted">Access and refresh token auditing.</p>
        </div>
        <div className="panel stat">
          <strong>OpenPGP</strong>
          <p className="muted">Optional mailbox-level PGP support.</p>
        </div>
      </div>
    </section>
  );
}
