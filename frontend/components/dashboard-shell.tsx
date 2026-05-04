"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

const roles = ["SUPER_ADMIN", "DOMAIN_ADMIN", "USER"] as const;

const navigation = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/domains", label: "Domains" },
  { href: "/users", label: "Users" },
  { href: "/mailbox", label: "Mailbox" },
  { href: "/settings", label: "Settings" },
  { href: "/smtp", label: "SMTP" },
];

export function DashboardShell({
  children,
}: Readonly<{ children: ReactNode }>) {
  const pathname = usePathname();
  const [role, setRole] = useState<(typeof roles)[number]>("SUPER_ADMIN");

  useEffect(() => {
    const saved = window.localStorage.getItem("nexudo-role");
    if (saved && roles.includes(saved as (typeof roles)[number])) {
      setRole(saved as (typeof roles)[number]);
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("nexudo-role", role);
  }, [role]);

  const visibleNavigation = useMemo(() => {
    if (role === "USER") {
      return navigation.filter((item) =>
        ["/dashboard", "/mailbox", "/settings", "/smtp"].includes(item.href),
      );
    }
    if (role === "DOMAIN_ADMIN") {
      return navigation.filter((item) => item.href !== "/users" || true);
    }
    return navigation;
  }, [role]);

  return (
    <div className="page-shell">
      <aside className="sidebar">
        <div className="brand">Nexudo Mail</div>
        <p className="muted" style={{ marginTop: 10 }}>
          Role-aware control plane
        </p>
        <div className="nav-list">
          {visibleNavigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-link ${pathname === item.href ? "active" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </div>
        <div style={{ marginTop: 24 }} className="panel stat">
          <div className="muted">Current role</div>
          <select
            value={role}
            onChange={(event) =>
              setRole(event.target.value as (typeof roles)[number])
            }
            style={{
              width: "100%",
              marginTop: 10,
              background: "rgba(255,255,255,0.06)",
              color: "var(--text)",
              border: 0,
              borderRadius: 12,
              padding: 12,
            }}
          >
            {roles.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
