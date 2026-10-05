"use client";

// Building blocks shared by the Amazon integration feature sections.

import { ApiError } from "../../../lib/api";
import type { Marketplace } from "../config";

export type Status = { kind: "success" | "error"; text: string } | null;

export function formatDate(value: string) {
  // Backend stores naive UTC datetimes.
  const date = new Date(value.endsWith("Z") ? value : `${value}Z`);
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function errorText(err: unknown) {
  if (err instanceof ApiError && err.status === 401) {
    return "You are not signed in. Log in and try again.";
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong.";
}

export function latest(values: (string | null | undefined)[]) {
  return values.reduce<string | null>((max, v) => (v && (!max || v > max) ? v : max), null);
}

export function SyncButton({
  onClick,
  syncing,
  label,
}: {
  onClick: () => void;
  syncing: boolean;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={syncing}
      className="inline-flex items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <svg
        className={`h-4 w-4 ${syncing ? "animate-spin" : ""}`}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        aria-hidden="true"
      >
        <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v6h-6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {syncing ? "Syncing…" : label}
    </button>
  );
}

export function StatusBanner({ status }: { status: Status }) {
  if (!status) return null;
  return (
    <div
      role="status"
      className={`rounded-lg border px-4 py-3 text-sm ${
        status.kind === "success"
          ? "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300"
          : "border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300"
      }`}
    >
      {status.text}
    </div>
  );
}

export const TONE = {
  default: "text-zinc-900 dark:text-zinc-50",
  good: "text-emerald-600 dark:text-emerald-400",
  info: "text-sky-600 dark:text-sky-400",
  warn: "text-amber-600 dark:text-amber-400",
  bad: "text-rose-600 dark:text-rose-400",
};

export function StatCard({
  label,
  value,
  tone = TONE.default,
  loading,
}: {
  label: string;
  value: number;
  tone?: string;
  loading: boolean;
}) {
  return (
    <div className="rounded-2xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-black/20">
      <p className="text-sm text-zinc-500 dark:text-zinc-400">{label}</p>
      <p className={`mt-1 text-3xl font-semibold tabular-nums ${tone}`}>
        {loading ? "–" : value.toLocaleString()}
      </p>
    </div>
  );
}

export function MarketplaceTabs({
  marketplaces,
  selectedId,
  onSelect,
}: {
  marketplaces: Marketplace[];
  selectedId: string;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist" aria-label="Marketplace">
      {marketplaces.map((m) => {
        const active = m.id === selectedId;
        return (
          <button
            key={m.id}
            type="button"
            role="tab"
            aria-selected={active}
            title={`${m.name} · ${m.id}`}
            onClick={() => onSelect(m.id)}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${
              active
                ? "border-indigo-600 bg-indigo-600 text-white shadow-sm"
                : "border-zinc-300 bg-white text-zinc-700 hover:border-indigo-400 hover:text-indigo-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
            }`}
          >
            {m.code}
          </button>
        );
      })}
    </div>
  );
}
