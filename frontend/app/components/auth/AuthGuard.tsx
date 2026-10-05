"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearSession, fetchMe, getToken, type User } from "../../lib/auth";
import { AppShell } from "../shell/AppShell";

/** Renders children inside the app shell for a signed-in user; otherwise redirects to /login?next=<current path>. */
export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const toLogin = () => {
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      router.replace(`/login?next=${next}`);
    };
    if (!getToken()) return toLogin();
    // Verifies the token with the backend; apiFetch redirects on 401.
    fetchMe().then(setUser).catch(() => {});
  }, [router]);

  function handleLogout() {
    clearSession();
    router.replace("/login");
  }

  if (!user) {
    return (
      <div className="flex min-h-screen flex-1 items-center justify-center bg-zinc-50 dark:bg-zinc-950">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <AppShell user={user} onLogout={handleLogout}>
      {children}
    </AppShell>
  );
}
