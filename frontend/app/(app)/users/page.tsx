export default function UsersPage() {
  return (
    <section className="hero">
      <div className="toolbar">
        <div>
          <div className="pill">Identity</div>
          <h1
            style={{ fontFamily: "var(--font-display)", margin: "12px 0 6px" }}
          >
            Users
          </h1>
          <div className="muted">
            Manage mailbox users, domain admins, and login activity.
          </div>
        </div>
        <button className="button">Invite User</button>
      </div>
      <table className="table">
        <thead>
          <tr>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th>Last Login</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>admin@sudoinnovation.tech</td>
            <td>SUPER_ADMIN</td>
            <td>Active</td>
            <td>2m ago</td>
          </tr>
          <tr>
            <td>ops@sudoinnovation.tech</td>
            <td>DOMAIN_ADMIN</td>
            <td>Active</td>
            <td>11m ago</td>
          </tr>
          <tr>
            <td>alice@sudoinnovation.tech</td>
            <td>USER</td>
            <td>Active</td>
            <td>45m ago</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
