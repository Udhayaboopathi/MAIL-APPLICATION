export function LogTable({
  rows,
}: Readonly<{
  rows: Array<{
    id: string;
    apiKey: string;
    recipient: string;
    status: string;
    latency: string;
  }>;
}>) {
  return (
    <section className="panel" style={{ padding: 20 }}>
      <div className="toolbar">
        <div>
          <strong>SMTP logs</strong>
          <div className="muted">Per API key delivery telemetry</div>
        </div>
        <button className="button secondary">Export</button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Log ID</th>
            <th>API Key</th>
            <th>Recipient</th>
            <th>Status</th>
            <th>Latency</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>{row.id}</td>
              <td>{row.apiKey}</td>
              <td>{row.recipient}</td>
              <td>{row.status}</td>
              <td>{row.latency}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
