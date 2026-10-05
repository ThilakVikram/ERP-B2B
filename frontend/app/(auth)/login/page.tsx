"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { login, redirectTarget } from "../../lib/auth";
import {
  Divider,
  FormError,
  FormField,
  GoogleButton,
  SubmitButton,
} from "../../components/auth/FormField";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    setError(null);
    setSubmitting(true);
    try {
      await login(
        String(form.get("email")),
        String(form.get("password")),
        form.get("remember") === "on",
      );
      router.replace(redirectTarget());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not log in.");
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Welcome back
        </h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Log in to your account to continue.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormError message={error} />
        <FormField
          id="email"
          label="Email"
          type="email"
          placeholder="you@company.com"
          autoComplete="email"
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          placeholder="••••••••"
          autoComplete="current-password"
        />

        <div className="flex items-center justify-between text-sm">
          <label className="flex items-center gap-2 text-zinc-600 dark:text-zinc-400">
            <input
              type="checkbox"
              name="remember"
              className="h-4 w-4 rounded border-zinc-300 accent-indigo-600"
            />
            Remember me
          </label>
          <a
            href="#"
            className="font-medium text-indigo-600 hover:text-indigo-500"
          >
            Forgot password?
          </a>
        </div>

        <SubmitButton disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </SubmitButton>
      </form>

      <Divider />
      <GoogleButton />

      <p className="mt-8 text-center text-sm text-zinc-600 dark:text-zinc-400">
        Don&apos;t have an account?{" "}
        <Link
          href="/signup"
          className="font-medium text-indigo-600 hover:text-indigo-500"
        >
          Sign up
        </Link>
      </p>
    </div>
  );
}
