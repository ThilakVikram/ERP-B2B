"use client";

// /reports/orders: stored order rows per marketplace, and the scheduler for
// GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL.

import { useEffect, useState } from "react";
import { getOrderItemsSummary, getOrderReportCoverage, scheduleOrderReports, type OrderItemsSummary } from "../../api";
import { errorText, formatDate, type Status } from "../shared";
import { useReports } from "./context";
import { MarketplaceOverview } from "./MarketplaceOverview";
import { ScheduleReports } from "./ScheduleReports";
import { longDate } from "./shared";

export function OrderReports() {
  const { region, marketplaces, selectedId, select, version, markQueued } = useReports();
  const [summary, setSummary] = useState<OrderItemsSummary[] | null>(null);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    let cancelled = false;
    getOrderItemsSummary()
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
  const sum = (key: "rowCount" | "orderCount") => [...byId.values()].reduce((n, s) => n + s[key], 0);

  return (
    <>
      <MarketplaceOverview
        title="Marketplace overview"
        hint="Pick a marketplace to see its stored order rows. Scheduling below uses the same marketplace."
        status={status}
        badge={(id) => ({ text: loading ? "–" : `${(byId.get(id)?.rowCount ?? 0).toLocaleString()} rows`, muted: !byId.get(id) })}
        regionTotals={[
          { label: "rows", value: num(sum("rowCount")) },
          { label: "orders", value: num(sum("orderCount")) },
        ]}
        tiles={[
          { label: "Total rows", value: num(stats?.rowCount), big: true },
          { label: "Total orders", value: num(stats?.orderCount), big: true },
          {
            label: "Purchase dates",
            value:
              stats?.firstPurchaseDate && stats.lastPurchaseDate
                ? `${longDate(stats.firstPurchaseDate)} – ${longDate(stats.lastPurchaseDate)}`
                : loading ? "–" : "No orders stored",
          },
          { label: "Last stored", value: stats?.lastStoredAt ? formatDate(stats.lastStoredAt) : loading ? "–" : "Never" },
        ]}
      />
      <ScheduleReports
        title="Schedule report queue"
        hint="Pick a date range on the calendar, choose how many days each report covers, and queue them. Reports run one at a time."
        noun="report"
        schedule={scheduleOrderReports}
        getCoverage={getOrderReportCoverage}
        marketplaces={marketplaces}
        marketplaceId={selectedId}
        onMarketplaceChange={select}
        version={version}
        onQueued={markQueued}
      />
    </>
  );
}
