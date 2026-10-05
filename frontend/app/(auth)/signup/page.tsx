"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { signup, redirectTarget } from "../../lib/auth";
import {
  Divider,
  FormError,
  FormField,
  GoogleButton,
  SubmitButton,
} from "../../components/auth/FormField";

export default function SignupPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const password = String(form.get("password"));
    const confirmPassword = String(form.get("confirmPassword"));
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await signup({
        firstName: String(form.get("firstName")),
        lastName: String(form.get("lastName")),
        email: String(form.get("email")),
        password,
        confirmPassword,
      });
      router.replace(redirectTarget());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account.");
      setSubmitting(false);
    }
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Create your account
        </h1>
        <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          Get started with iTrend in less than a minute.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <FormError message={error} />
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
          <FormField
            id="firstName"
            label="First name"
            placeholder="John"
            autoComplete="given-name"
          />
          <FormField
            id="lastName"
            label="Last name"
            placeholder="Doe"
            autoComplete="family-name"
          />
        </div>
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
          placeholder="At least 8 characters"
          autoComplete="new-password"
          minLength={8}
        />
        <FormField
          id="confirmPassword"
          label="Confirm password"
          type="password"
          placeholder="Re-enter your password"
          autoComplete="new-password"
          minLength={8}
        />

        <label className="flex items-start gap-2 text-sm text-zinc-600 dark:text-zinc-400">
          <input
            type="checkbox"
            name="terms"
            required
            className="mt-0.5 h-4 w-4 rounded border-zinc-300 accent-indigo-600"
          />
          <span>
            I agree to the{" "}
            <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="font-medium text-indigo-600 hover:text-indigo-500">
              Privacy Policy
            </a>
          </span>
        </label>

        <SubmitButton disabled={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </SubmitButton>
      </form>

      <Divider />
      <GoogleButton />

      <p className="mt-8 text-center text-sm text-zinc-600 dark:text-zinc-400">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-indigo-600 hover:text-indigo-500"
        >
          Log in
        </Link>
      </p>
    </div>
  );
}
