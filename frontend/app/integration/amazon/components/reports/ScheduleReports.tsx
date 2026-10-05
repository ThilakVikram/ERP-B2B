"use client";

import { useEffect, useMemo, useState } from "react";
import type { ReportBatch, ReportCoverage, ScheduleRequest } from "../../api";
import type { Marketplace } from "../../config";
import { StatusBanner, errorText, type Status } from "../shared";
import { MARK_STYLES, MonthCalendar, monthOf, type DayMark } from "./RangeCalendar";
import {
  CARD,
  INPUT,
  MAX_PARTITION_DAYS,
  MAX_SCHEDULE_DAYS,
  SectionTitle,
  addDays,
  daysBetween,
  fromIso,
  longDate,
  partition,
  shortDate,
  today,
  toIso,
  type Period,
} from "./shared";

const PARTITION_CHIPS = [1, 7, 10, 15, 30];
const PREVIEW_LIMIT = 40;

function thisMonday() {
  const t = today();
  return addDays(t, -((new Date(fromIso(t)).getUTCDay() + 6) % 7));
}

function firstOfMonth(monthsAgo: number) {
  const d = new Date(fromIso(today()));
  return toIso(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() - monthsAgo, 1));
}

const PRESETS: { label: string; range: () => [string, string] }[] = [
  { label: "Last 7 days", range: () => [addDays(today(), -6), today()] },
  { label: "Last week", range: () => [addDays(thisMonday(), -7), addDays(thisMonday(), -1)] },
  { label: "This month", range: () => [firstOfMonth(0), today()] },
  { label: "Last month", range: () => [firstOfMonth(1), addDays(firstOfMonth(0), -1)] },
  { label: "Last 90 days", range: () => [addDays(today(), -89), today()] },
  { label: "Year to date", range: () => [`${today().slice(0, 4)}-01-01`, today()] },
];

function markDays(coverage: ReportCoverage | null): Map<string, DayMark> {
  const marks = new Map<string, DayMark>();
  const add = (periods: { startDate: string; endDate: string }[], mark: DayMark) => {
    for (const p of periods) for (let d = p.startDate; d <= p.endDate; d = addDays(d, 1)) marks.set(d, mark);
  };
  // A day covered by several requests shows the most relevant status: later ones win.
  add(coverage?.cancelled ?? [], "CANCELLED");
  add(coverage?.failed ?? [], "FAILED");
  add(coverage?.synced ?? [], "SYNCED");
  add(coverage?.queued ?? [], "QUEUED");
  add(coverage?.processing ?? [], "PROCESSING");
  return marks;
}

export function ScheduleReports({
  title,
  hint,
  noun,
  schedule,
  getCoverage,
  marketplaces,
  marketplaceId,
  onMarketplaceChange,
  version,
  onQueued,
}: {
  marketplaces: Marketplace[];
  marketplaceId: string; // shared with the marketplace overview
  onMarketplaceChange: (marketplaceId: string) => void;
  version: number; // bumped when the queue moves: reload what is already covered
  onQueued: (ids: number[]) => void;
  title: string;
  hint: string;
  noun: string; // what one queued request is, e.g. "report" or "query"
  schedule: (request: ScheduleRequest) => Promise<ReportBatch>;
  getCoverage: (marketplaceId: string) => Promise<ReportCoverage>; // days already queued / fetched
}) {
  const plural = (n: number) => (n === 1 ? noun : noun.endsWith("y") ? `${noun.slice(0, -1)}ies` : `${noun}s`);
  const max = today();
  const [[start, end], setRangeState] = useState<[string, string]>(() => PRESETS[0].range());
  const [fromMonth, setFromMonth] = useState(() => monthOf(PRESETS[0].range()[0]));
  const [toMonth, setToMonth] = useState(() => monthOf(max));
  const [partitionDays, setPartitionDays] = useState(7);
  const [coverage, setCoverage] = useState<{ marketplaceId: string; data: ReportCoverage } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [status, setStatus] = useState<Status>(null);

  const marketplace = marketplaces.find((m) => m.id === marketplaceId) ?? marketplaces[0];

  useEffect(() => {
    let cancelled = false;
    getCoverage(marketplace.id)
      .then((data) => !cancelled && setCoverage({ marketplaceId: marketplace.id, data }))
      .catch(() => {}); // highlighting is a hint; scheduling still works without it
    return () => {
      cancelled = true;
    };
  }, [getCoverage, marketplace.id, version]);

  // Ignore coverage of the previously selected marketplace while the new one loads.
  const marks = useMemo(
    () => markDays(coverage?.marketplaceId === marketplace.id ? coverage.data : null),
    [coverage, marketplace.id],
  );
  const markOf = (day: string) => marks.get(day) ?? null;

  const totalDays = daysBetween(start, end);
  const tooLong = totalDays > MAX_SCHEDULE_DAYS;
  const periods: Period[] = tooLong ? [] : partition(start, end, partitionDays);
  const overlap = useMemo(() => {
    const counts = { inQueue: 0, requested: 0 };
    if (!tooLong) for (let d = start; d <= end; d = addDays(d, 1)) {
      const m = marks.get(d);
      if (m === "SYNCED") counts.requested += 1;
      else if (m === "QUEUED" || m === "PROCESSING") counts.inQueue += 1;
    }
    return counts;
  }, [marks, start, end, tooLong]);

  function setRange(s: string, e: string, moveMonths = false) {
    setRangeState([s, e]);
    setStatus(null);
    if (moveMonths) {
      setFromMonth(monthOf(s));
      setToMonth(monthOf(e));
    }
  }

  // Left calendar sets From, right calendar sets To; crossing over moves the other end along.
  function pickFrom(day: string) {
    if (day > end) {
      setRange(day, day);
      setToMonth(monthOf(day));
    } else setRange(day, end);
  }

  function pickTo(day: string) {
    if (day < start) {
      setRange(day, day);
      setFromMonth(monthOf(day));
    } else setRange(start, day);
  }

  function setPartition(value: number) {
    if (Number.isFinite(value)) setPartitionDays(Math.min(MAX_PARTITION_DAYS, Math.max(1, Math.round(value))));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setStatus(null);
    try {
      const { queued, skipped } = await schedule({
        marketplaceId: marketplace.id,
        startDate: start,
        endDate: end,
        partitionDays,
      });
      const parts = [];
      if (queued.length) {
        parts.push(
          `Queued ${queued.length} ${plural(queued.length)} for ${marketplace.code} ` +
            `(requests #${queued[0].id}${queued.length > 1 ? `–#${queued[queued.length - 1].id}` : ""}).`,
        );
      }
      if (skipped.length) {
        parts.push(
          `${skipped.length} period${skipped.length === 1 ? " was" : "s were"} already queued or processing: ` +
            skipped.map((s) => `${shortDate(s.startDate)} – ${shortDate(s.endDate)}`).join(", ") + ".",
        );
      }
      setStatus({ kind: queued.length ? "success" : "error", text: parts.join(" ") });
      onQueued(queued.map((r) => r.id));
    } catch (err) {
      setStatus({ kind: "error", text: errorText(err) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <SectionTitle
        step={2}
        title={title}
        hint={hint}
      />
      <form onSubmit={handleSubmit} className={`${CARD} grid grid-cols-1 lg:grid-cols-[1fr_20rem]`}>
        {/* Calendar */}
        <div className="space-y-4 border-b border-zinc-200 p-5 lg:border-b-0 lg:border-r dark:border-zinc-800">
          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => {
              const [s, e] = p.range();
              const active = s === start && e === end;
              return (
                <button
                  key={p.label}
                  type="button"
                  onClick={() => setRange(s, e, true)}
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                    active
                      ? "border-indigo-600 bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                      : "border-zinc-300 text-zinc-700 hover:border-indigo-400 hover:text-indigo-600 dark:border-zinc-700 dark:text-zinc-300"
                  }`}
                >
                  {p.label}
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <MonthCalendar
              title="From"
              picks="start"
              start={start}
              end={end}
              max={max}
              partitionDays={partitionDays}
              month={fromMonth}
              onMonthChange={setFromMonth}
              markOf={markOf}
              onPick={pickFrom}
            />
            <MonthCalendar
              title="To"
              picks="end"
              start={start}
              end={end}
              max={max}
              partitionDays={partitionDays}
              month={toMonth}
              onMonthChange={setToMonth}
              markOf={markOf}
              onPick={pickTo}
            />
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-zinc-600 dark:text-zinc-400">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded bg-indigo-600" /> Selected range
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3.5 w-3.5 rounded bg-emerald-100 ring-1 ring-inset ring-indigo-500 dark:bg-emerald-900/40" /> Covered day
              inside the range
            </span>
            {(Object.keys(MARK_STYLES) as DayMark[]).map((m) => (
              <span key={m} className="flex items-center gap-1.5">
                <span className={`relative h-3.5 w-3.5 rounded ${MARK_STYLES[m].day}`}>
                  <span className={`absolute bottom-0.5 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full ${MARK_STYLES[m].dot}`} />
                </span>
                {MARK_STYLES[m].label} for {marketplace.code}
              </span>
            ))}
          </div>
        </div>

        {/* Options + preview */}
        <div className="flex flex-col gap-5 p-5">
          <label className="flex flex-col gap-1.5 text-sm font-medium text-zinc-700 dark:text-zinc-300">
            Marketplace
            <select value={marketplace.id} onChange={(e) => onMarketplaceChange(e.target.value)} className={INPUT}>
              {marketplaces.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.code} · {m.name}
                </option>
              ))}
            </select>
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="partition-days" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
                Days per {noun}
              </label>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  min={1}
                  max={MAX_PARTITION_DAYS}
                  value={partitionDays}
                  onChange={(e) => setPartition(e.target.valueAsNumber)}
                  aria-label={`Days per ${noun}`}
                  className={`${INPUT} w-16 py-1 text-center`}
                />
                <span className="text-sm text-zinc-500">days</span>
              </div>
            </div>
            <input
              id="partition-days"
              type="range"
              min={1}
              max={MAX_PARTITION_DAYS}
              value={partitionDays}
              onChange={(e) => setPartition(e.target.valueAsNumber)}
              className="w-full accent-indigo-600"
            />
            <div className="flex flex-wrap gap-1.5">
              {PARTITION_CHIPS.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setPartitionDays(d)}
                  className={`rounded-md px-2 py-0.5 text-xs font-medium transition ${
                    d === partitionDays
                      ? "bg-indigo-600 text-white"
                      : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300"
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 rounded-lg bg-zinc-50 p-3 dark:bg-zinc-950/50">
            {tooLong ? (
              <p className="text-sm text-rose-600 dark:text-rose-400">
                {totalDays} days selected — one schedule can cover at most {MAX_SCHEDULE_DAYS} days.
              </p>
            ) : (
              <>
                <p className="text-sm text-zinc-700 dark:text-zinc-300">
                  <span className="font-medium">{longDate(start)} – {longDate(end)}</span> · {totalDays} day
                  {totalDays === 1 ? "" : "s"}
                </p>
                <p className="mt-0.5 text-sm text-zinc-500">
                  {periods.length} {plural(periods.length)} of up to {partitionDays} day
                  {partitionDays === 1 ? "" : "s"}:
                </p>
                <ol className="mt-2 max-h-48 space-y-1 overflow-y-auto pr-1">
                  {periods.slice(0, PREVIEW_LIMIT).map((p, i) => (
                    <li key={p.start} className="flex items-center gap-2 font-mono text-xs text-zinc-700 dark:text-zinc-300">
                      <span className={`h-2 w-2 shrink-0 rounded-full ${i % 2 ? "bg-violet-400" : "bg-indigo-500"}`} />
                      {shortDate(p.start)} – {shortDate(p.end)}
                      <span className="text-zinc-400">({daysBetween(p.start, p.end)}d)</span>
                    </li>
                  ))}
                  {periods.length > PREVIEW_LIMIT && (
                    <li className="text-xs text-zinc-500">…and {periods.length - PREVIEW_LIMIT} more</li>
                  )}
                </ol>
                {(overlap.inQueue > 0 || overlap.requested > 0) && (
                  <p className="mt-2 rounded-md bg-amber-50 px-2 py-1.5 text-xs text-amber-800 dark:bg-amber-950/50 dark:text-amber-300">
                    {[
                      overlap.requested && `${overlap.requested} day${overlap.requested === 1 ? " is" : "s are"} already fetched`,
                      overlap.inQueue && `${overlap.inQueue} day${overlap.inQueue === 1 ? " is" : "s are"} already in the queue`,
                    ]
                      .filter(Boolean)
                      .join(" and ")}
                    . Queuing requests them again; stored order items are not duplicated.
                  </p>
                )}
              </>
            )}
          </div>

          <button
            type="submit"
            disabled={submitting || periods.length === 0}
            className="rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting
              ? "Queuing…"
              : periods.length
                ? `Queue ${periods.length} ${plural(periods.length)} for ${marketplace.code}`
                : `Queue ${plural(2)}`}
          </button>
          <StatusBanner status={status} />
        </div>
      </form>
    </div>
  );
}
