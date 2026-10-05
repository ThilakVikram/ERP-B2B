"use client";

import { useEffect, useState } from "react";
import {
  listMarketplaceParticipations,
  syncMarketplaceParticipations,
  type MarketplaceParticipation,
} from "../api";
import type { FeatureProps } from "../config";
import {
  StatCard,
  StatusBanner,
  SyncButton,
  TONE,
  errorText,
  formatDate,
  latest,
  type Status,
} from "./shared";

export function MarketplaceParticipations({ region }: FeatureProps) {
  const [rows, setRows] = useState<MarketplaceParticipation[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    listMarketplaceParticipations(region.code)
      .then((data) => !cancelled && setRows(data))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [region.code]);

  async function handleSync() {
    setSyncing(true);
    setStatus(null);
    try {
      const result = await syncMarketplaceParticipations(region.code);
      setRows(result.participations);
      setStatus({
        kind: "success",
        text: `Synced ${result.count} marketplace${result.count === 1 ? "" : "s"} for ${region.name}.`,
      });
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSyncing(false);
    }
  }

  const participating = rows.filter((r) => r.isParticipating).length;
  const suspended = rows.filter((r) => r.hasSuspendedListings).length;
  const lastSynced = latest(rows.map((r) => r.lastSyncedAt));

  const stats = [
    { label: "Marketplaces", value: rows.length },
    { label: "Participating", value: participating, tone: TONE.good },
    { label: "Suspended listings", value: suspended, tone: suspended ? TONE.bad : TONE.default },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          {lastSynced ? `Last synced ${formatDate(lastSynced)}` : "Not synced yet"}
        </p>
        <SyncButton onClick={handleSync} syncing={syncing} label={`Sync ${region.code} from Amazon`} />
      </div>

      <StatusBanner status={status} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} loading={loading} />
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        {loading ? (
          <div className="space-y-3 p-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800" />
            ))}
          </div>
        ) : rows.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="font-medium text-zinc-900 dark:text-zinc-100">
              No marketplaces stored for {region.name}
            </p>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Run a sync to fetch them from Amazon.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
                <tr>
                  <th className="px-5 py-3 font-medium">Marketplace</th>
                  <th className="px-5 py-3 font-medium">Store</th>
                  <th className="px-5 py-3 font-medium">Currency / Language</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {rows.map((r) => (
                  <tr key={r.id} className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-indigo-50 text-xs font-semibold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                          {r.countryCode}
                        </span>
                        <div>
                          <p className="font-medium text-zinc-900 dark:text-zinc-100">{r.name}</p>
                          <p className="font-mono text-xs text-zinc-500">{r.marketplaceId}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">
                      {r.storeName ?? <span className="text-zinc-400">—</span>}
                      <p className="text-xs text-zinc-500">{r.domainName}</p>
                    </td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">
                      {r.defaultCurrencyCode}
                      <span className="text-zinc-400"> · </span>
                      {r.defaultLanguageCode}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            r.isParticipating
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                          }`}
                        >
                          {r.isParticipating ? "Participating" : "Not participating"}
                        </span>
                        {r.hasSuspendedListings && (
                          <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-950 dark:text-rose-300">
                            Suspended listings
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
