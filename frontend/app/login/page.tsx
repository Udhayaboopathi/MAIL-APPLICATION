"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { useRouter } from "next/navigation";

import { apiFetch } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useAuthStore } from "../../store/auth-store";

export default function LoginPage() {
  const router = useRouter();
  const setSession = useAuthStore((state) => state.setSession);
  const [email, setEmail] = useState("admin@sudoinnovation.tech");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    try {
      const response = await apiFetch<{
        access_token: string;
        refresh_token: string;
        token_type: string;
      }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setSession({
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
        email,
      });
      window.localStorage.setItem("nexudo-access-token", response.access_token);
      window.localStorage.setItem(
        "nexudo-refresh-token",
        response.refresh_token,
      );
      router.push("/mail/inbox");
    } catch {
      setError("Login failed. Check the backend seed user or credentials.");
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[radial-gradient(circle_at_top_left,rgba(37,99,235,0.08),transparent_28%),linear-gradient(180deg,#ffffff_0%,#f7f9fb_100%)] px-4 text-text">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-[32px] border border-slate-200 bg-white p-8 shadow-[0_24px_80px_rgba(15,23,42,0.10)]"
      >
        <div className="font-display text-4xl font-semibold tracking-tight text-slate-900">
          Nexudo Mail
        </div>
        <p className="mt-2 text-sm text-slate-500">
          Sign in to your mailbox, domain admin, or super admin workspace.
        </p>
        <div className="mt-6 space-y-4">
          <Input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
          />
          <Input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            type="password"
          />
          {error ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              {error}
            </div>
          ) : null}
          <Button className="w-full">Login</Button>
        </div>
      </form>
    </main>
  );
}
