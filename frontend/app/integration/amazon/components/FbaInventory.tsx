"use client";

import { useEffect, useMemo, useState } from "react";
import {
  listInventorySummaries,
  syncInventorySummaries,
  type FbaInventorySummary,
} from "../api";
import type { FeatureProps, Marketplace } from "../config";
import {
  MarketplaceTabs,
  StatCard,
  StatusBanner,
  SyncButton,
  TONE,
  errorText,
  formatDate,
  latest,
  type Status,
} from "./shared";

const PAGE_SIZE = 25;

const inbound = (r: FbaInventorySummary) =>
  r.inboundWorkingQuantity + r.inboundShippedQuantity + r.inboundReceivingQuantity;

// Numeric columns of the table; also the sortable ones.
const COLUMNS: { key: string; label: string; value: (r: FbaInventorySummary) => number; tone?: string }[] = [
  { key: "total", label: "Total", value: (r) => r.totalQuantity },
  { key: "fulfillable", label: "Fulfillable", value: (r) => r.fulfillableQuantity, tone: TONE.good },
  { key: "inbound", label: "Inbound", value: inbound, tone: TONE.info },
  { key: "reserved", label: "Reserved", value: (r) => r.totalReservedQuantity, tone: TONE.warn },
  { key: "unfulfillable", label: "Unfulfillable", value: (r) => r.totalUnfulfillableQuantity, tone: TONE.bad },
];

export function FbaInventory({ region }: FeatureProps) {
  const [marketplaceId, setMarketplaceId] = useState(region.marketplaces[0].id);
  const marketplace =
    region.marketplaces.find((m) => m.id === marketplaceId) ?? region.marketplaces[0];

  return (
    <div className="space-y-6">
      <MarketplaceTabs
        marketplaces={region.marketplaces}
        selectedId={marketplace.id}
        onSelect={setMarketplaceId}
      />

      {/* Keyed so each marketplace starts with fresh state and its own fetch. */}
      <MarketplaceInventory key={marketplace.id} marketplace={marketplace} />
    </div>
  );
}

function MarketplaceInventory({ marketplace }: { marketplace: Marketplace }) {
  const [rows, setRows] = useState<FbaInventorySummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [status, setStatus] = useState<Status>(null);
  const [query, setQuery] = useState("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [sortKey, setSortKey] = useState("total");
  const [page, setPage] = useState(0);

  useEffect(() => {
    let cancelled = false;
    listInventorySummaries(marketplace.id)
      .then((data) => !cancelled && setRows(data))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [marketplace.id]);

  async function handleSync() {
    setSyncing(true);
    setStatus(null);
    try {
      const result = await syncInventorySummaries(marketplace.id);
      setRows(await listInventorySummaries(marketplace.id));
      setPage(0);
      setStatus({
        kind: "success",
        text: `Synced ${result.count.toLocaleString()} SKU${result.count === 1 ? "" : "s"} for ${marketplace.name}.`,
      });
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSyncing(false);
    }
  }

  const totals = useMemo(
    () => ({
      skus: rows.length,
      units: rows.reduce((n, r) => n + r.totalQuantity, 0),
      fulfillable: rows.reduce((n, r) => n + r.fulfillableQuantity, 0),
      inbound: rows.reduce((n, r) => n + inbound(r), 0),
      reserved: rows.reduce((n, r) => n + r.totalReservedQuantity, 0),
      unfulfillable: rows.reduce((n, r) => n + r.totalUnfulfillableQuantity, 0),
    }),
    [rows],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const sortValue = COLUMNS.find((c) => c.key === sortKey)!.value;
    return rows
      .filter((r) => !inStockOnly || r.totalQuantity > 0)
      .filter(
        (r) =>
          !q ||
          [r.sellerSku, r.asin, r.fnSku, r.productName].some((v) => v?.toLowerCase().includes(q)),
      )
      .sort((a, b) => sortValue(b) - sortValue(a) || a.sellerSku.localeCompare(b.sellerSku));
  }, [rows, query, inStockOnly, sortKey]);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount - 1);
  const visible = filtered.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE);
  const lastSynced = latest(rows.map((r) => r.lastSyncedAt));

  const stats = [
    { label: "SKUs", value: totals.skus },
    { label: "Total units", value: totals.units },
    { label: "Fulfillable", value: totals.fulfillable, tone: TONE.good },
    { label: "Inbound", value: totals.inbound, tone: TONE.info },
    { label: "Reserved", value: totals.reserved, tone: TONE.warn },
    { label: "Unfulfillable", value: totals.unfulfillable, tone: totals.unfulfillable ? TONE.bad : TONE.default },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-medium text-zinc-900 dark:text-zinc-100">
            {marketplace.name}{" "}
            <span className="font-mono text-xs font-normal text-zinc-500">{marketplace.id}</span>
          </p>
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            {lastSynced ? `Last synced ${formatDate(lastSynced)}` : "Not synced yet"}
          </p>
        </div>
        <SyncButton onClick={handleSync} syncing={syncing} label={`Sync ${marketplace.code} inventory`} />
      </div>

      {syncing && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          Fetching every page from Amazon. Large catalogs can take a minute.
        </p>
      )}
      <StatusBanner status={status} />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} loading={loading} />
        ))}
      </div>

      <div className="overflow-hidden rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex flex-col gap-3 border-b border-zinc-200 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-zinc-800">
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="Search SKU, ASIN, FNSKU or product name"
            className="w-full rounded-lg border border-zinc-300 bg-white px-3.5 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 sm:max-w-sm dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100"
          />
          <label className="flex items-center gap-2 text-sm text-zinc-600 dark:text-zinc-400">
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(e) => {
                setInStockOnly(e.target.checked);
                setPage(0);
              }}
              className="h-4 w-4 rounded border-zinc-300 accent-indigo-600"
            />
            In stock only
          </label>
        </div>

        {loading ? (
          <div className="space-y-3 p-6">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800" />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <div className="px-6 py-14 text-center">
            <p className="font-medium text-zinc-900 dark:text-zinc-100">
              {rows.length ? "No SKUs match your filters" : `No inventory stored for ${marketplace.name}`}
            </p>
            <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
              {rows.length ? "Try a different search." : "Run a sync to fetch it from Amazon."}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950/40 dark:text-zinc-400">
                <tr>
                  <th className="px-5 py-3 font-medium">Product</th>
                  {COLUMNS.map((c) => (
                    <th key={c.key} className="px-4 py-3 text-right font-medium">
                      <button
                        type="button"
                        onClick={() => {
                          setSortKey(c.key);
                          setPage(0);
                        }}
                        className={`whitespace-nowrap uppercase tracking-wide transition hover:text-zinc-900 dark:hover:text-zinc-100 ${
                          sortKey === c.key ? "text-indigo-600 dark:text-indigo-400" : ""
                        }`}
                      >
                        {c.label}
                        {sortKey === c.key && " ↓"}
                      </button>
                    </th>
                  ))}
                  <th className="px-5 py-3 font-medium">Updated</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {visible.map((r) => (
                  <tr key={r.id} className="transition hover:bg-zinc-50 dark:hover:bg-zinc-800/50">
                    <td className="max-w-md px-5 py-3.5">
                      <p className="truncate font-medium text-zinc-900 dark:text-zinc-100" title={r.productName ?? ""}>
                        {r.productName ?? "Untitled product"}
                      </p>
                      <p className="mt-0.5 flex flex-wrap gap-x-3 font-mono text-xs text-zinc-500">
                        <span>{r.sellerSku}</span>
                        {r.asin && <span>ASIN {r.asin}</span>}
                        {r.fnSku && <span>FNSKU {r.fnSku}</span>}
                      </p>
                    </td>
                    {COLUMNS.map((c) => {
                      const v = c.value(r);
                      return (
                        <td
                          key={c.key}
                          className={`px-4 py-3.5 text-right tabular-nums ${
                            v === 0 ? "text-zinc-300 dark:text-zinc-600" : c.tone ?? "font-medium text-zinc-900 dark:text-zinc-100"
                          }`}
                        >
                          {v.toLocaleString()}
                        </td>
                      );
                    })}
                    <td className="whitespace-nowrap px-5 py-3.5 text-xs text-zinc-500">
                      {r.lastUpdatedTime ? formatDate(r.lastUpdatedTime) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && filtered.length > PAGE_SIZE && (
          <div className="flex items-center justify-between border-t border-zinc-200 px-5 py-3 text-sm text-zinc-500 dark:border-zinc-800">
            <span>
              {(currentPage * PAGE_SIZE + 1).toLocaleString()}–
              {Math.min((currentPage + 1) * PAGE_SIZE, filtered.length).toLocaleString()} of{" "}
              {filtered.length.toLocaleString()}
            </span>
            <div className="flex gap-2">
              {[
                { label: "Previous", to: currentPage - 1, disabled: currentPage === 0 },
                { label: "Next", to: currentPage + 1, disabled: currentPage >= pageCount - 1 },
              ].map((b) => (
                <button
                  key={b.label}
                  type="button"
                  disabled={b.disabled}
                  onClick={() => setPage(b.to)}
                  className="rounded-lg border border-zinc-300 px-3 py-1.5 font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
                >
                  {b.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
