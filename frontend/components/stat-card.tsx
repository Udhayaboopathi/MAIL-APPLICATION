export function StatCard({
  label,
  value,
  detail,
}: Readonly<{ label: string; value: string; detail: string }>) {
  return (
    <section className="panel stat">
      <div className="muted">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="muted">{detail}</div>
    </section>
  );
}
