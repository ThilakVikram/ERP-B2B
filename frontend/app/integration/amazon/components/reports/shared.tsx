"use client";

// Helpers shared by the Reports sections: UTC dates, status labels and small layout pieces.

import type { AmazonReport, ReportSyncStatus } from "../../api";

export const DAY_MS = 86_400_000;
export const MAX_PARTITION_DAYS = 30; // Amazon's limit per orders report
export const MAX_SCHEDULE_DAYS = 366; // backend limit for one schedule

export const CARD =
  "overflow-hidden rounded-2xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-black/20";
export const TH = "px-5 py-3 font-medium";
export const INPUT =
  "rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100";

// ---------- Dates: plain YYYY-MM-DD strings in UTC ----------

export const toIso = (ms: number) => new Date(ms).toISOString().slice(0, 10);
export const fromIso = (iso: string) => Date.parse(`${iso.slice(0, 10)}T00:00:00Z`);
export const addDays = (iso: string, days: number) => toIso(fromIso(iso) + days * DAY_MS);
export const today = () => toIso(Date.now());
export const daysBetween = (start: string, end: string) => Math.round((fromIso(end) - fromIso(start)) / DAY_MS) + 1;

export const shortDate = (iso: string) =>
  new Date(fromIso(iso)).toLocaleDateString(undefined, { month: "short", day: "numeric", timeZone: "UTC" });
export const longDate = (iso: string) =>
  new Date(fromIso(iso)).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });

export type Period = { start: string; end: string };

// Same split as the backend: consecutive `days`-day periods from the start; the last may be shorter.
export function partition(start: string, end: string, days: number): Period[] {
  const periods: Period[] = [];
  for (let day = start; day <= end; day = addDays(day, days)) {
    const last = addDays(day, days - 1);
    periods.push({ start: day, end: last < end ? last : end });
  }
  return periods;
}

export const reportPeriod = (r: AmazonReport) =>
  REPORT_KINDS[r.reportType]?.snapshot
    ? `Snapshot · ${shortDate(r.dataStartTime)}`
    : `${shortDate(r.dataStartTime)} – ${shortDate(r.dataEndTime)}`;

// ---------- Status ----------

// Per report type: display name, whether it is a snapshot (no data period), and what the
// report's skippedCount means for it.
export const REPORT_KINDS: Record<string, { label: string; snapshot: boolean; existing: string }> = {
  GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL: { label: "All orders by order date", snapshot: false, existing: "skipped" },
  GET_MERCHANT_LISTINGS_ALL_DATA: { label: "All listings", snapshot: true, existing: "updated" },
  DATA_KIOSK_SKU_ECONOMICS: { label: "SKU Economics (Data Kiosk)", snapshot: false, existing: "updated" },
};

export const reportLabel = (reportType: string) => REPORT_KINDS[reportType]?.label ?? reportType;

export const STATUS_STYLES: Record<ReportSyncStatus, string> = {
  QUEUED: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  PROCESSING: "bg-sky-50 text-sky-700 dark:bg-sky-950 dark:text-sky-300",
  SYNCED: "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  FAILED: "bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
  CANCELLED: "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
};

// Steps of one report while PROCESSING, keyed by Amazon's processing status.
export const STEPS: { key: string | null; label: string }[] = [
  { key: null, label: "Requesting from Amazon" },
  { key: "IN_QUEUE", label: "Queued at Amazon" },
  { key: "IN_PROGRESS", label: "Amazon is generating" },
  { key: "DONE", label: "Saving rows" },
];

export function stageText(r: AmazonReport): string {
  switch (r.syncStatus) {
    case "QUEUED":
      return r.queuePosition ? `Waiting · #${r.queuePosition} in line` : "Waiting in queue";
    case "PROCESSING":
      return STEPS.find((s) => s.key === r.processingStatus)?.label ?? `Amazon: ${r.processingStatus}`;
    case "SYNCED": {
      if (r.error) return REPORT_KINDS[r.reportType]?.snapshot ? "Amazon returned no data" : "No orders in this period";
      const existing = REPORT_KINDS[r.reportType]?.existing ?? "skipped";
      return `${r.insertedCount.toLocaleString()} new, ${r.skippedCount.toLocaleString()} ${existing}`;
    }
    case "FAILED":
      return "Failed";
    case "CANCELLED":
      return "Cancelled before it started";
  }
}

export function StatusBadge({ status }: { status: ReportSyncStatus }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
      {status === "PROCESSING" && <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-current" />}
      {status.charAt(0) + status.slice(1).toLowerCase()}
    </span>
  );
}

// ---------- Layout ----------

export function SectionTitle({ step, title, hint }: { step?: number; title: string; hint?: string }) {
  return (
    <div className="mb-3 flex items-start gap-3">
      {step !== undefined && (
        <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-xs font-semibold text-white">
          {step}
        </span>
      )}
      <div>
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-50">{title}</h3>
        {hint && <p className="text-sm text-zinc-500 dark:text-zinc-400">{hint}</p>}
      </div>
    </div>
  );
}

export function EmptyState({ title, hint }: { title: string; hint: React.ReactNode }) {
  return (
    <div className="px-6 py-10 text-center">
      <p className="font-medium text-zinc-900 dark:text-zinc-100">{title}</p>
      <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">{hint}</p>
    </div>
  );
}

export function LoadingRows({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3 p-6">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="h-10 animate-pulse rounded-lg bg-zinc-100 dark:bg-zinc-800" />
      ))}
    </div>
  );
}
