"use client";

import { useEffect, useState } from "react";
import type { RegionCode } from "../../../integration/amazon/config";
import {
  StatCard,
  StatusBanner,
  TONE,
  errorText,
  formatDate,
  latest,
  type Status,
} from "../../../integration/amazon/components/shared";
import { listAmazonMarketplaces, syncAmazonMarketplaces, type AmazonMarketplace, type SyncMode } from "../api";
import { RegionFilter } from "./RegionFilter";
import { SyncActions } from "./SyncActions";

export function Marketplaces() {
  const [region, setRegion] = useState<RegionCode | null>(null);
  const [rows, setRows] = useState<AmazonMarketplace[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<SyncMode | null>(null);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    listAmazonMarketplaces(region)
      .then((data) => !cancelled && setRows(data))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [region]);

  function changeRegion(next: RegionCode | null) {
    setLoading(true);
    setStatus(null);
    setRegion(next);
  }

  async function handleSync(mode: SyncMode) {
    setSyncing(mode);
    setStatus(null);
    try {
      const result = await syncAmazonMarketplaces(region, mode);
      setRows(result.marketplaces);
      const total = result.created + result.updated;
      const label = mode === "full" ? "Full sync" : "Sync";
      setStatus(
        total > 0
          ? { kind: "success", text: `${label}: created ${result.created}, updated ${result.updated} marketplace${total === 1 ? "" : "s"}.` }
          : mode === "normal" && result.marketplaces.length > 0
            ? { kind: "success", text: "Sync: every marketplace participation is already linked. Use Full sync to refresh them." }
            : { kind: "error", text: "No marketplace participations stored. Sync them under Integrations → Amazon → Marketplaces first." },
      );
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSyncing(null);
    }
  }

  const active = rows.filter((r) => r.isActive).length;
  const unlinked = rows.filter((r) => r.integrationId === null).length;
  const lastUpdated = latest(rows.map((r) => r.updatedAt));

  const stats = [
    { label: "Marketplaces", value: rows.length },
    { label: "Active", value: active, tone: TONE.good },
    { label: "Not linked to integration", value: unlinked, tone: unlinked ? TONE.warn : TONE.default },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <RegionFilter value={region} onChange={changeRegion} />
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {lastUpdated ? `Last updated ${formatDate(lastUpdated)}` : "Not synced yet"}
          </p>
        </div>
        <SyncActions syncing={syncing} onSync={handleSync} scope={region ?? "all regions"} />
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
            <p className="font-medium text-zinc-900 dark:text-zinc-100">No marketplaces yet</p>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              Run a sync to create them from the integration&apos;s marketplace participations.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
                <tr>
                  <th className="px-5 py-3 font-medium">Marketplace</th>
                  <th className="px-5 py-3 font-medium">Region</th>
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
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">{r.region}</td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">
                      {r.storeName ?? <span className="text-zinc-400">—</span>}
                      <p className="text-xs text-zinc-500">{r.domainName}</p>
                    </td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">
                      {r.currencyCode}
                      <span className="text-zinc-400"> · </span>
                      {r.languageCode}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                            r.isActive
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                          }`}
                        >
                          {r.isActive ? "Active" : "Inactive"}
                        </span>
                        {r.integrationId === null && (
                          <span className="rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                            Not linked
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
