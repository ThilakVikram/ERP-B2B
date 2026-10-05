"use client";

// Marketplace switcher + stats for the selected marketplace. Each report route passes its own
// numbers (order rows, listings, ...); the selected marketplace is shared through useReports().

import { StatusBanner, type Status } from "../shared";
import { useReports } from "./context";
import { CARD, SectionTitle } from "./shared";

export type Tile = { label: string; value: string; big?: boolean };

export function MarketplaceOverview({
  title,
  hint,
  badge,
  regionTotals,
  tiles,
  status,
}: {
  title: string;
  hint: string;
  badge: (marketplaceId: string) => { text: string; muted: boolean }; // shown on each switcher button
  regionTotals: { label: string; value: string }[];
  tiles: Tile[]; // for the selected marketplace
  status?: Status;
}) {
  const { region, marketplaces, selectedId, select } = useReports();
  const selected = marketplaces.find((m) => m.id === selectedId) ?? marketplaces[0];

  return (
    <div>
      <SectionTitle step={1} title={title} hint={hint} />
      <div className="space-y-3">
        <StatusBanner status={status ?? null} />
        <div className={CARD}>
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-200 px-5 py-4 dark:border-zinc-800">
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-600 px-2 py-0.5 text-xs font-semibold text-white">{region.code}</span>
              <p className="font-semibold text-zinc-900 dark:text-zinc-50">{region.name}</p>
            </div>
            <p className="text-sm text-zinc-500">
              Region total:{" "}
              {regionTotals.map((t, i) => (
                <span key={t.label}>
                  {i > 0 && " · "}
                  <span className="font-semibold tabular-nums text-zinc-900 dark:text-zinc-100">{t.value}</span> {t.label}
                </span>
              ))}
            </p>
          </div>

          <div
            role="tablist"
            aria-label="Marketplace"
            className="grid grid-cols-2 gap-2 border-b border-zinc-200 p-4 sm:grid-cols-3 lg:grid-cols-5 dark:border-zinc-800"
          >
            {marketplaces.map((m) => {
              const active = m.id === selected.id;
              const b = badge(m.id);
              return (
                <button
                  key={m.id}
                  type="button"
                  role="tab"
                  aria-selected={active}
                  onClick={() => select(m.id)}
                  title={`${m.name} · ${m.id}`}
                  className={`rounded-lg border px-3 py-2.5 text-left transition ${
                    active
                      ? "border-indigo-600 bg-indigo-50 shadow-sm dark:bg-indigo-950/60"
                      : "border-zinc-200 hover:border-indigo-400 dark:border-zinc-700"
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-sm font-semibold ${active ? "text-indigo-700 dark:text-indigo-300" : "text-zinc-900 dark:text-zinc-100"}`}>
                      {m.code}
                    </span>
                    <span className={`text-xs tabular-nums ${b.muted ? "text-zinc-400" : "text-zinc-600 dark:text-zinc-300"}`}>
                      {b.text}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-zinc-500">{m.name}</p>
                </button>
              );
            })}
          </div>

          <div className="p-5">
            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
              {selected.name} <span className="font-mono text-xs font-normal text-zinc-500">{selected.id}</span>
            </p>
            <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
              {tiles.map((t) => (
                <div key={t.label} className="rounded-lg bg-zinc-50 p-4 dark:bg-zinc-950/50">
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">{t.label}</p>
                  <p
                    className={`mt-1 tabular-nums text-zinc-900 dark:text-zinc-50 ${
                      t.big ? "text-3xl font-semibold" : "text-sm font-medium"
                    }`}
                  >
                    {t.value}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
