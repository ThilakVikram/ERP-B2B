"use client";

// /data_kiosk/economics: stored SKU economics per marketplace, and scheduling the Data Kiosk
// SKU Economics query (analytics_economics_2024_03_15) over a date range. The marketplace
// overview, scheduler and queue panel are the Reports section's components, pointed at the Data Kiosk queue.

import { useEffect, useState } from "react";
import {
  getSkuEconomicsCoverage,
  getSkuEconomicsSummary,
  scheduleSkuEconomics,
  type SkuEconomicsSummary,
} from "../../api";
import { useReports } from "../reports/context";
import { MarketplaceOverview } from "../reports/MarketplaceOverview";
import { ScheduleReports } from "../reports/ScheduleReports";
import { longDate } from "../reports/shared";
import { errorText, formatDate, type Status } from "../shared";

function money(amount: string | number, currency: string | null) {
  const value = Number(amount);
  if (!currency) return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  try {
    return value.toLocaleString(undefined, { style: "currency", currency, maximumFractionDigits: 2 });
  } catch {
    return `${currency} ${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
  }
}

export function SkuEconomics() {
  const { region, marketplaces, selectedId, select, version, markQueued } = useReports();
  const [summary, setSummary] = useState<SkuEconomicsSummary[] | null>(null);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    getSkuEconomicsSummary()
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
  const none = loading ? "–" : "Not fetched yet";

  return (
    <>
      <MarketplaceOverview
        title="Marketplace overview"
        hint="Pick a marketplace to see its stored SKU economics (sales, fees, ad spend and net proceeds). Scheduling below uses the same marketplace."
        status={status}
        badge={(id) => ({
          text: loading ? "–" : `${(byId.get(id)?.skuCount ?? 0).toLocaleString()} SKUs`,
          muted: !byId.get(id),
        })}
        regionTotals={[
          { label: "SKU periods", value: num([...byId.values()].reduce((n, s) => n + s.rowCount, 0)) },
          { label: "SKUs", value: num([...byId.values()].reduce((n, s) => n + s.skuCount, 0)) },
        ]}
        tiles={[
          { label: "Net product sales", value: stats ? money(stats.netProductSales, stats.currencyCode) : none, big: true },
          { label: "Net proceeds", value: stats ? money(stats.netProceedsTotal, stats.currencyCode) : none, big: true },
          {
            label: "SKUs / net units sold",
            value: stats ? `${stats.skuCount.toLocaleString()} SKUs · ${stats.netUnitsSold.toLocaleString()} units` : none,
          },
          {
            label: "Periods covered",
            value:
              stats?.firstDate && stats.lastDate
                ? `${longDate(stats.firstDate)} – ${longDate(stats.lastDate)}${
                    stats.lastUpdatedAt ? ` · updated ${formatDate(stats.lastUpdatedAt)}` : ""
                  }`
                : none,
          },
        ]}
      />
      <ScheduleReports
        title="Schedule SKU Economics queries"
        hint="Pick a date range, choose how many days each query covers, and queue them. Each query returns every SKU's economics for its period; queries run one at a time in the Data Kiosk queue, independently of reports."
        noun="query"
        schedule={scheduleSkuEconomics}
        getCoverage={getSkuEconomicsCoverage}
        marketplaces={marketplaces}
        marketplaceId={selectedId}
        onMarketplaceChange={select}
        version={version}
        onQueued={markQueued}
      />
    </>
  );
}
