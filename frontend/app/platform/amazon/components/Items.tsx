"use client";

import { useEffect, useState } from "react";
import type { RegionCode } from "../../../integration/amazon/config";
import {
  StatCard,
  StatusBanner,
  TONE,
  errorText,
  type Status,
} from "../../../integration/amazon/components/shared";
import {
  listAmazonItems,
  listAmazonMarketplaces,
  syncAmazonItems,
  type AmazonItem,
  type AmazonMarketplace,
  type SyncMode,
} from "../api";
import { RegionFilter } from "./RegionFilter";
import { SyncActions } from "./SyncActions";

const PAGE_SIZE = 100;

export function Items() {
  const [region, setRegion] = useState<RegionCode | null>(null);
  const [marketplaces, setMarketplaces] = useState<AmazonMarketplace[]>([]);
  const [marketplaceId, setMarketplaceId] = useState<number | null>(null);
  const [search, setSearch] = useState(""); // what is typed
  const [q, setQ] = useState(""); // what is queried, after a pause in typing
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<{ total: number; items: AmazonItem[] }>({ total: 0, items: [] });
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState<SyncMode | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    listAmazonMarketplaces(region)
      .then((data) => !cancelled && setMarketplaces(data))
      .catch(() => {}); // the items request below reports errors
    return () => {
      cancelled = true;
    };
  }, [region, reloadKey]);

  useEffect(() => {
    let cancelled = false;
    listAmazonItems({ region, amazonMarketplaceId: marketplaceId, q, limit: PAGE_SIZE, offset })
      .then((data) => !cancelled && setPage(data))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [region, marketplaceId, q, offset, reloadKey]);

  useEffect(() => {
    if (search.trim() === q) return;
    const timer = setTimeout(() => {
      setLoading(true);
      setOffset(0);
      setQ(search.trim());
    }, 300);
    return () => clearTimeout(timer);
  }, [search, q]);

  function changeRegion(next: RegionCode | null) {
    setLoading(true);
    setStatus(null);
    setRegion(next);
    setMarketplaceId(null);
    setOffset(0);
  }

  function changeMarketplace(next: number | null) {
    setLoading(true);
    setMarketplaceId(next);
    setOffset(0);
  }

  function changeOffset(next: number) {
    setLoading(true);
    setOffset(next);
  }

  async function handleSync(mode: SyncMode) {
    setSyncing(mode);
    setStatus(null);
    try {
      const result = await syncAmazonItems(region, mode);
      const skipped = result.skipped
        ? ` ${result.skipped.toLocaleString()} listing${result.skipped === 1 ? "" : "s"} skipped: their marketplace is not created yet (sync Marketplaces first).`
        : "";
      const label = mode === "full" ? "Full sync" : "Sync";
      const nothingNew = mode === "normal" && result.created + result.updated + result.skipped === 0;
      setStatus({
        kind: result.created + result.updated === 0 && result.skipped ? "error" : "success",
        text: nothingNew
          ? "Sync: every listing is already linked to an item. Use Full sync to refresh them."
          : `${label}: created ${result.created.toLocaleString()}, updated ${result.updated.toLocaleString()} items.${skipped}`,
      });
      setLoading(true);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSyncing(null);
    }
  }

  const unlinked = page.items.filter((i) => i.integrationId === null).length;
  const stats = [
    { label: "Items", value: page.total },
    { label: "Marketplaces", value: marketplaces.length, tone: TONE.info },
    { label: "Not linked on this page", value: unlinked, tone: unlinked ? TONE.warn : TONE.default },
  ];
  const from = page.total ? offset + 1 : 0;
  const to = Math.min(offset + PAGE_SIZE, page.total);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <RegionFilter value={region} onChange={changeRegion} />
        <SyncActions syncing={syncing} onSync={handleSync} scope={region ?? "all regions"} />
      </div>

      <StatusBanner status={status} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} loading={loading} />
        ))}
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <select
          value={marketplaceId ?? ""}
          onChange={(e) => changeMarketplace(e.target.value ? Number(e.target.value) : null)}
          aria-label="Marketplace"
          className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        >
          <option value="">All marketplaces</option>
          {marketplaces.map((m) => (
            <option key={m.id} value={m.id}>
              {m.countryCode} · {m.name}
            </option>
          ))}
        </select>
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search SKU, ASIN or title"
          aria-label="Search items"
          className="w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 sm:max-w-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        />
      </div>

      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        {loading ? (
          <div className="space-y-3 p-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800" />
            ))}
          </div>
        ) : page.items.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="font-medium text-zinc-900 dark:text-zinc-100">No items found</p>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {q || marketplaceId
                ? "Try another marketplace or search."
                : "Run a sync to create them from the integration's listings."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
                <tr>
                  <th className="px-5 py-3 font-medium">Item</th>
                  <th className="px-5 py-3 font-medium">Marketplace</th>
                  <th className="px-5 py-3 font-medium">ASIN</th>
                  <th className="px-5 py-3 font-medium">Fulfillment</th>
                  <th className="px-5 py-3 text-right font-medium">Price</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {page.items.map((i) => (
                  <tr key={i.id} className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="max-w-md px-5 py-4">
                      <p className="truncate font-medium text-zinc-900 dark:text-zinc-100" title={i.title ?? undefined}>
                        {i.title ?? <span className="text-zinc-400">—</span>}
                      </p>
                      <p className="font-mono text-xs text-zinc-500">{i.sellerSku}</p>
                    </td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300" title={i.marketplace.name}>
                      {i.marketplace.countryCode}
                      <span className="text-zinc-400"> · </span>
                      {i.marketplace.region}
                    </td>
                    <td className="px-5 py-4 font-mono text-xs text-zinc-700 dark:text-zinc-300">
                      {i.asin ?? <span className="text-zinc-400">—</span>}
                    </td>
                    <td className="px-5 py-4 text-zinc-700 dark:text-zinc-300">
                      {i.fulfillmentChannel ?? <span className="text-zinc-400">—</span>}
                    </td>
                    <td className="px-5 py-4 text-right tabular-nums text-zinc-700 dark:text-zinc-300">
                      {i.price !== null ? `${i.price} ${i.currencyCode ?? ""}` : <span className="text-zinc-400">—</span>}
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1.5">
                        {i.status && (
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              i.status === "Active"
                                ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
                                : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                            }`}
                          >
                            {i.status}
                          </span>
                        )}
                        {i.integrationId === null && (
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
        {page.total > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-zinc-200 px-5 py-3 text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
            <span>
              {from.toLocaleString()}–{to.toLocaleString()} of {page.total.toLocaleString()}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={offset === 0 || loading}
                onClick={() => changeOffset(Math.max(0, offset - PAGE_SIZE))}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 font-medium text-zinc-700 transition hover:border-indigo-400 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Previous
              </button>
              <button
                type="button"
                disabled={to >= page.total || loading}
                onClick={() => changeOffset(offset + PAGE_SIZE)}
                className="rounded-lg border border-zinc-300 px-3 py-1.5 font-medium text-zinc-700 transition hover:border-indigo-400 hover:text-indigo-600 disabled:cursor-not-allowed disabled:opacity-50 dark:border-zinc-700 dark:text-zinc-300"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
