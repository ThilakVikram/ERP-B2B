"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  type AmazonReport,
  type JobQueueApi,
  type ReportFilters,
  type ReportQueue,
  type ReportSyncStatus,
} from "../../api";
import { StatusBanner, errorText, formatDate, type Status } from "../shared";
import {
  CARD,
  EmptyState,
  INPUT,
  LoadingRows,
  REPORT_KINDS,
  STATUS_STYLES,
  STEPS,
  SectionTitle,
  StatusBadge,
  TH,
  reportLabel,
  reportPeriod,
  stageText,
} from "./shared";
import { useReports } from "./context";

const QUEUE_POLL_MS = 5000;

const COUNT_TILES: { status: ReportSyncStatus; label: string; tone: string }[] = [
  { status: "PROCESSING", label: "Processing", tone: "text-sky-600 dark:text-sky-400" },
  { status: "QUEUED", label: "Waiting", tone: "text-zinc-900 dark:text-zinc-50" },
  { status: "SYNCED", label: "Synced", tone: "text-emerald-600 dark:text-emerald-400" },
  { status: "FAILED", label: "Failed", tone: "text-rose-600 dark:text-rose-400" },
  { status: "CANCELLED", label: "Cancelled", tone: "text-amber-600 dark:text-amber-400" },
];

/** A backend queue (`api`: reports or Data Kiosk; all regions, all types) and, with `history`, this
 * region's request history. Polls while mounted; when the queue moves it bumps the shared version so other
 * sections refetch. */
export function QueueStatus({
  api,
  reportTypes,
  history = true,
}: {
  api: JobQueueApi;
  reportTypes: string[];
  history?: boolean;
}) {
  const { version, refresh: onChange, label } = useReports();
  const [queue, setQueue] = useState<ReportQueue | null>(null);
  const [status, setStatus] = useState<Status>(null);
  const signature = useRef<string | null>(null);

  const load = useCallback(
    () =>
      api
        .getQueue()
        .then((q) => {
          setQueue(q);
          const sig = [q.current?.id, q.current?.processingStatus, ...q.pending.map((p) => p.id)].join(",");
          if (signature.current !== null && signature.current !== sig) onChange();
          signature.current = sig;
        })
        .catch((err) => setStatus({ kind: "error", text: errorText(err) })),
    [api, onChange],
  );

  useEffect(() => {
    load();
    const timer = setInterval(load, QUEUE_POLL_MS);
    return () => clearInterval(timer);
  }, [load, version]);

  async function handleCancel(id: number) {
    try {
      await api.cancel(id);
      setStatus({ kind: "success", text: `Cancelled request #${id}.` });
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    }
    load();
  }

  const current = queue?.current;

  return (
    <div>
      <SectionTitle
        step={3}
        title="Queue status"
        hint={`What the backend is running now and what is waiting, across all regions. Refreshes every ${QUEUE_POLL_MS / 1000}s.`}
      />
      <div className="space-y-4">
        <StatusBanner status={status} />

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          {COUNT_TILES.map((t) => (
            <div key={t.status} className={`${CARD} p-4`}>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">{t.label}</p>
              <p className={`mt-1 text-2xl font-semibold tabular-nums ${t.tone}`}>
                {queue ? (queue.counts[t.status] ?? 0).toLocaleString() : "–"}
              </p>
            </div>
          ))}
        </div>

        <div className={CARD}>
          {!queue ? (
            <LoadingRows count={2} />
          ) : (
            <>
              <div className="border-b border-zinc-200 p-5 dark:border-zinc-800">
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">Processing now</p>
                {current ? (
                  <>
                    <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className="font-medium text-zinc-900 dark:text-zinc-100">
                          #{current.id} · {reportLabel(current.reportType)}
                        </p>
                        <p className="text-sm text-zinc-500">
                          {current.region} · {label(current.marketplaceId)} · {reportPeriod(current)}
                          {current.startedAt && ` · started ${formatDate(current.startedAt)}`}
                        </p>
                      </div>
                      <StatusBadge status={current.syncStatus} />
                    </div>
                    <StepProgress report={current} />
                  </>
                ) : (
                  <p className="mt-2 text-sm text-zinc-500">Idle — no {api.noun} is being processed.</p>
                )}
              </div>

              <div className="p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
                  Waiting ({queue.pending.length})
                </p>
                {queue.pending.length === 0 ? (
                  <p className="mt-2 text-sm text-zinc-500">Nothing waiting.</p>
                ) : (
                  <ol className="mt-2 max-h-80 divide-y divide-zinc-100 overflow-y-auto dark:divide-zinc-800">
                    {queue.pending.map((r) => (
                      <li key={r.id} className="flex items-center justify-between gap-3 py-2.5">
                        <div className="flex items-center gap-3">
                          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-zinc-100 text-xs font-semibold text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                            {r.queuePosition}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-zinc-900 dark:text-zinc-100">
                              #{r.id} · {label(r.marketplaceId)} · {reportPeriod(r)}
                            </p>
                            <p className="text-xs text-zinc-500">
                              {r.region} · {reportLabel(r.reportType)} · requested {formatDate(r.createdAt)}
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCancel(r.id)}
                          className="rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:border-rose-300 hover:bg-rose-50 hover:text-rose-700 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-rose-950"
                        >
                          Cancel
                        </button>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            </>
          )}
        </div>

        {history && <ReportHistory api={api} reportTypes={reportTypes} />}
      </div>
    </div>
  );
}

function StepProgress({ report }: { report: AmazonReport }) {
  const current = Math.max(0, STEPS.findIndex((s) => s.key === report.processingStatus));
  return (
    <ol className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
      {STEPS.map((s, i) => (
        <li key={s.label} className="flex flex-col gap-1.5">
          <span
            className={`h-1.5 rounded-full ${
              i < current ? "bg-indigo-600" : i === current ? "animate-pulse bg-indigo-400" : "bg-zinc-200 dark:bg-zinc-800"
            }`}
          />
          <span className={`text-xs ${i <= current ? "font-medium text-zinc-900 dark:text-zinc-100" : "text-zinc-500"}`}>
            {s.label}
          </span>
        </li>
      ))}
    </ol>
  );
}

const HISTORY_LIMIT = 100;
const ALL_STATUSES: ReportSyncStatus[] = ["QUEUED", "PROCESSING", "SYNCED", "FAILED", "CANCELLED"];

/** History of this region's requests of `reportTypes` (the section's types); filterable. */
export function ReportHistory({
  api,
  reportTypes,
  emptyHint = "Queue some above.",
}: {
  api: JobQueueApi;
  reportTypes: string[];
  emptyHint?: string;
}) {
  const { region, marketplaces, version, label, justQueued: highlight } = useReports();
  const [marketplaceId, setMarketplaceId] = useState("");
  const [reportType, setReportType] = useState("");
  const [statuses, setStatuses] = useState<ReportSyncStatus[]>([]);
  const [result, setResult] = useState<{ key: string; rows: AmazonReport[] } | null>(null);
  const [status, setStatus] = useState<Status>(null);

  // Identifies the filters a result was fetched for.
  const key = JSON.stringify([marketplaceId, reportType, statuses]);
  const filtered = Boolean(marketplaceId || reportType || statuses.length);

  useEffect(() => {
    let cancelled = false;
    const filters: ReportFilters = { marketplaceId, reportTypes: reportType ? [reportType] : reportTypes, statuses };
    api
      .list(region.code, filters, HISTORY_LIMIT)
      .then((rows) => !cancelled && setResult({ key, rows }))
      .catch((err) => !cancelled && setStatus({ kind: "error", text: errorText(err) }));
    return () => {
      cancelled = true;
    };
  }, [api, region.code, marketplaceId, reportType, reportTypes, statuses, key, version]);

  // Keep showing the previous rows while a refresh for the same filters loads; blank on a filter change.
  const rows = result?.key === key ? result.rows : null;

  function toggleStatus(s: ReportSyncStatus) {
    setStatuses((current) => (current.includes(s) ? current.filter((x) => x !== s) : [...current, s]));
  }

  function clearFilters() {
    setMarketplaceId("");
    setReportType("");
    setStatuses([]);
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium text-zinc-700 dark:text-zinc-300">Request history · {region.name}</p>
      <StatusBanner status={status} />
      <div className={CARD}>
        <div className="flex flex-col gap-3 border-b border-zinc-200 p-4 lg:flex-row lg:items-end lg:justify-between dark:border-zinc-800">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:flex lg:items-end">
            <label className="flex flex-col gap-1 text-xs font-medium text-zinc-600 dark:text-zinc-400">
              Marketplace
              <select value={marketplaceId} onChange={(e) => setMarketplaceId(e.target.value)} className={`${INPUT} py-1.5`}>
                <option value="">All marketplaces</option>
                {marketplaces.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.code} · {m.name}
                  </option>
                ))}
              </select>
            </label>
            {reportTypes.length > 1 && (
              <label className="flex flex-col gap-1 text-xs font-medium text-zinc-600 dark:text-zinc-400">
                Report type
                <select value={reportType} onChange={(e) => setReportType(e.target.value)} className={`${INPUT} py-1.5`}>
                  <option value="">All report types</option>
                  {reportTypes.map((type) => (
                    <option key={type} value={type}>
                      {REPORT_KINDS[type]?.label ?? type}
                    </option>
                  ))}
                </select>
              </label>
            )}
            <div className="flex flex-col gap-1 sm:col-span-2">
              <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400">Status</span>
              <div className="flex flex-wrap gap-1.5" role="group" aria-label="Status">
                {ALL_STATUSES.map((s) => {
                  const on = statuses.includes(s);
                  return (
                    <button
                      key={s}
                      type="button"
                      aria-pressed={on}
                      onClick={() => toggleStatus(s)}
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 transition ${
                        on
                          ? `${STATUS_STYLES[s]} ring-current`
                          : "text-zinc-500 ring-zinc-300 hover:text-zinc-800 dark:ring-zinc-700 dark:hover:text-zinc-200"
                      }`}
                    >
                      {s.charAt(0) + s.slice(1).toLowerCase()}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-zinc-500">
            {rows && (
              <span>
                {rows.length === HISTORY_LIMIT ? `Latest ${HISTORY_LIMIT}` : `${rows.length} request${rows.length === 1 ? "" : "s"}`}
                {filtered && " matching"}
              </span>
            )}
            {filtered && (
              <button type="button" onClick={clearFilters} className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                Clear filters
              </button>
            )}
          </div>
        </div>
        {!rows ? (
          <LoadingRows />
        ) : rows.length === 0 ? (
          filtered ? (
            <EmptyState title="No requests match these filters" hint="Change or clear the filters." />
          ) : (
            <EmptyState title={`No ${api.noun} requests for ${region.name} yet`} hint={emptyHint} />
          )
        ) : (
          <div className="max-h-[32rem] overflow-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="sticky top-0 border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-400">
                <tr>
                  <th className={TH}>Request</th>
                  <th className={TH}>Marketplace</th>
                  <th className={TH}>Period</th>
                  <th className={TH}>Status</th>
                  <th className={`${TH} text-right`}>Rows</th>
                  <th className={`${TH} text-right`}>New</th>
                  <th className={`${TH} text-right`} title="Orders: rows already stored (skipped). Listings: SKUs updated.">
                    Skipped / updated
                  </th>
                  <th className={TH}>Finished</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {rows.map((r) => (
                  <tr
                    key={r.id}
                    className={`align-top transition hover:bg-zinc-50 dark:hover:bg-zinc-800/50 ${
                      highlight.includes(r.id) ? "bg-indigo-50/60 dark:bg-indigo-950/30" : ""
                    }`}
                  >
                    <td className="whitespace-nowrap px-5 py-3.5">
                      <p className="font-medium text-zinc-900 dark:text-zinc-100">#{r.id}</p>
                      <p className="text-xs text-indigo-600 dark:text-indigo-400">{reportLabel(r.reportType)}</p>
                      <p className="text-xs text-zinc-500">{formatDate(r.createdAt)}</p>
                    </td>
                    <td className="whitespace-nowrap px-5 py-3.5 text-zinc-700 dark:text-zinc-300">{label(r.marketplaceId)}</td>
                    <td className="whitespace-nowrap px-5 py-3.5 text-zinc-600 dark:text-zinc-400">{reportPeriod(r)}</td>
                    <td className="max-w-xs px-5 py-3.5">
                      <StatusBadge status={r.syncStatus} />
                      <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">{stageText(r)}</p>
                      {r.syncStatus === "FAILED" && r.error && (
                        <p className="mt-1 line-clamp-2 text-xs text-rose-600 dark:text-rose-400" title={r.error}>
                          {r.error}
                        </p>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums">{r.rowCount.toLocaleString()}</td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-emerald-600 dark:text-emerald-400">
                      {r.insertedCount.toLocaleString()}
                    </td>
                    <td className="px-5 py-3.5 text-right tabular-nums text-zinc-500">{r.skippedCount.toLocaleString()}</td>
                    <td className="whitespace-nowrap px-5 py-3.5 text-xs text-zinc-500">
                      {r.completedAt ? formatDate(r.completedAt) : "—"}
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
