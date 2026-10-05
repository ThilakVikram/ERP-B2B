"use client";

// /reports/listings: stored listings per marketplace, and requesting
// GET_MERCHANT_LISTINGS_ALL_DATA snapshots.

import { useEffect, useState } from "react";
import { getListingsSummary, requestListingReports, type ListingsSummary } from "../../api";
import { StatusBanner, errorText, formatDate, type Status } from "../shared";
import { useReports } from "./context";
import { MarketplaceOverview } from "./MarketplaceOverview";
import { CARD, SectionTitle } from "./shared";

export function ListingReports() {
  const { region, version, selectedId } = useReports();
  const [summary, setSummary] = useState<ListingsSummary[] | null>(null);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    getListingsSummary()
      .then((data) => !cancelled && setSummary(data))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }));
    return () => {
      cancelled = true;
    };
  }, [version]);

  const loading = summary === null;
  const byId = new Map((summary ?? []).filter((s) => s.region === region.code).map((s) => [s.marketplaceId, s]));
  const stats = byId.get(selectedId);
  const num = (v: number | undefined) => (loading ? "–" : (v ?? 0).toLocaleString());
  const sum = (key: "listingCount" | "activeCount") => [...byId.values()].reduce((n, s) => n + s[key], 0);

  return (
    <>
      <MarketplaceOverview
        title="Marketplace overview"
        hint="Pick a marketplace to see its stored listings. Requests below use the same marketplace."
        status={status}
        badge={(id) => ({
          text: loading ? "–" : `${(byId.get(id)?.listingCount ?? 0).toLocaleString()} SKUs`,
          muted: !byId.get(id),
        })}
        regionTotals={[
          { label: "listings", value: num(sum("listingCount")) },
          { label: "active", value: num(sum("activeCount")) },
        ]}
        tiles={[
          { label: "Total listings", value: num(stats?.listingCount), big: true },
          { label: "Active listings", value: num(stats?.activeCount), big: true },
          {
            label: "Inactive / units",
            value: stats
              ? `${(stats.listingCount - stats.activeCount).toLocaleString()} inactive · ${stats.totalQuantity.toLocaleString()} units`
              : loading ? "–" : "No listings stored",
          },
          { label: "Last updated", value: stats?.lastUpdatedAt ? formatDate(stats.lastUpdatedAt) : loading ? "–" : "Never" },
        ]}
      />
      <RequestListings />
    </>
  );
}

function RequestListings() {
  const { region, marketplaces, selectedId, markQueued } = useReports();
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<Status>(null);
  const selected = marketplaces.find((m) => m.id === selectedId) ?? marketplaces[0];

  async function request(ids: string[]) {
    setSubmitting(true);
    setStatus(null);
    try {
      const { queued, skipped } = await requestListingReports(ids);
      const parts = [];
      if (queued.length) {
        parts.push(
          `Queued ${queued.length} listings snapshot${queued.length === 1 ? "" : "s"} ` +
            `(request${queued.length === 1 ? "" : "s"} #${queued.map((r) => r.id).join(", #")}).`,
        );
      }
      if (skipped.length) {
        parts.push(`Already queued or processing today: ${skipped.map((s) => s.reason.split(":")[0]).map(codeOf).join(", ")}.`);
      }
      setStatus({ kind: queued.length ? "success" : "error", text: parts.join(" ") });
      markQueued(queued.map((r) => r.id));
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSubmitting(false);
    }
  }

  function codeOf(id: string) {
    return marketplaces.find((m) => m.id === id)?.code ?? id;
  }

  const button =
    "rounded-lg px-4 py-2.5 text-sm font-semibold shadow-sm transition focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60";

  return (
    <div>
      <SectionTitle
        step={2}
        title="Request listings snapshot"
        hint="Amazon returns every listing (SKU) of the marketplace as it is now, active and inactive. New SKUs are added; stored ones are updated."
      />
      <div className={`${CARD} space-y-4 p-5`}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-medium text-zinc-900 dark:text-zinc-100">
              {selected.code} · {selected.name}
            </p>
            <p className="text-sm text-zinc-500">
              No date range: a snapshot always reflects the listings at the time Amazon generates it.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={submitting}
              onClick={() => request([selected.id])}
              className={`${button} bg-indigo-600 text-white hover:bg-indigo-500`}
            >
              {submitting ? "Queuing…" : `Snapshot ${selected.code}`}
            </button>
            {marketplaces.length > 1 && (
              <button
                type="button"
                disabled={submitting}
                onClick={() => request(marketplaces.map((m) => m.id))}
                className={`${button} border border-indigo-600 bg-white text-indigo-700 hover:bg-indigo-50 dark:bg-zinc-900 dark:text-indigo-300 dark:hover:bg-indigo-950`}
              >
                All {region.code} marketplaces ({marketplaces.length})
              </button>
            )}
          </div>
        </div>
        <StatusBanner status={status} />
      </div>
    </div>
  );
}
