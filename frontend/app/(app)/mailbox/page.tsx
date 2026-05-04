export default function MailboxPage() {
  return (
    <section className="hero">
      <div className="toolbar">
        <div>
          <div className="pill">Mailbox</div>
          <h1
            style={{ fontFamily: "var(--font-display)", margin: "12px 0 6px" }}
          >
            Mailbox workspace
          </h1>
          <div className="muted">
            Maildir-backed user experience with filters, labels, and templates.
          </div>
        </div>
        <button className="button secondary">Create Label</button>
      </div>
      <div className="grid two">
        <div className="panel stat">
          <strong>Inbox</strong>
          <p className="muted">124 unread messages</p>
        </div>
        <div className="panel stat">
          <strong>Templates</strong>
          <p className="muted">7 saved reply templates</p>
        </div>
      </div>
    </section>
  );
}
