"use client";

// One month of a date range picker (UTC days). The schedule uses two: the left one sets the
// "From" day and the right one sets the "To" day, each paged on its own. Both show the selected
// range (tinted per partition) and mark each day with the status of its requests, labelled and
// coloured as in the request history.

import type { ReportSyncStatus } from "../../api";
import { daysBetween, fromIso, toIso } from "./shared";

const WEEKDAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];

// Months are identified by their first day, "YYYY-MM-01".
export const monthOf = (iso: string) => `${iso.slice(0, 7)}-01`;
export function addMonths(month: string, n: number) {
  const d = new Date(fromIso(month));
  return toIso(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + n, 1));
}

function monthDays(month: string): (string | null)[] {
  const first = new Date(fromIso(month));
  const blanks = (first.getUTCDay() + 6) % 7; // weeks start on Monday
  const count = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
  return [
    ...Array<null>(blanks).fill(null),
    ...Array.from({ length: count }, (_, i) => `${month.slice(0, 8)}${String(i + 1).padStart(2, "0")}`),
  ];
}

export type DayMark = ReportSyncStatus;

// Same labels and hues as the history's StatusBadge (STATUS_STYLES in ./shared), a shade stronger.
export const MARK_STYLES: Record<DayMark, { label: string; day: string; dot: string }> = {
  PROCESSING: {
    label: "Processing",
    day: "bg-sky-100 text-sky-900 dark:bg-sky-900/40 dark:text-sky-100",
    dot: "bg-sky-500",
  },
  QUEUED: {
    label: "Queued",
    day: "bg-zinc-200 text-zinc-900 dark:bg-zinc-700/60 dark:text-zinc-100",
    dot: "bg-zinc-500",
  },
  SYNCED: {
    label: "Synced",
    day: "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/40 dark:text-emerald-100",
    dot: "bg-emerald-500",
  },
  FAILED: {
    label: "Failed",
    day: "bg-rose-100 text-rose-900 dark:bg-rose-900/40 dark:text-rose-100",
    dot: "bg-rose-500",
  },
  CANCELLED: {
    label: "Cancelled",
    day: "bg-amber-100 text-amber-900 dark:bg-amber-900/40 dark:text-amber-100",
    dot: "bg-amber-500",
  },
};

const PARTITION_TINTS = [
  "bg-indigo-100 text-indigo-900 dark:bg-indigo-900/60 dark:text-indigo-100",
  "bg-violet-100 text-violet-900 dark:bg-violet-900/50 dark:text-violet-100",
];

export function MonthCalendar({
  title,
  picks,
  start,
  end,
  max,
  partitionDays,
  month,
  onMonthChange,
  markOf,
  onPick,
}: {
  title: string;
  picks: "start" | "end"; // which end of the range a click sets
  start: string;
  end: string;
  max: string; // last selectable day
  partitionDays: number;
  month: string; // "YYYY-MM-01"
  onMonthChange: (month: string) => void;
  markOf: (day: string) => DayMark | null;
  onPick: (day: string) => void;
}) {
  const picked = picks === "start" ? start : end;

  function dayClass(day: string) {
    const base = "relative h-9 w-full text-sm tabular-nums transition";
    if (day > max) return `${base} cursor-not-allowed text-zinc-300 dark:text-zinc-700`;
    if (day === picked) return `${base} rounded-md bg-indigo-600 font-semibold text-white shadow-sm ring-2 ring-indigo-300 dark:ring-indigo-800`;
    if (day === start || day === end) return `${base} rounded-md bg-indigo-500/80 font-semibold text-white`;

    const mark = markOf(day);
    if (day > start && day < end) {
      const offset = daysBetween(start, day) - 1;
      const first = offset % partitionDays === 0;
      const last = offset % partitionDays === partitionDays - 1;
      // Covered days keep their highlight inside the range, outlined to show they are selected.
      const tint = mark
        ? `${MARK_STYLES[mark].day} ring-1 ring-inset ring-indigo-500`
        : PARTITION_TINTS[Math.floor(offset / partitionDays) % 2];
      return `${base} ${tint} ${first ? "rounded-l-md" : ""} ${last ? "rounded-r-md" : ""}`;
    }
    if (mark) return `${base} rounded-md ${MARK_STYLES[mark].day} hover:ring-2 hover:ring-indigo-300`;
    return `${base} rounded-md text-zinc-800 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800 ${
      day === max ? "font-semibold underline decoration-indigo-500 underline-offset-4" : ""
    }`;
  }

  return (
    <div className="select-none">
      <div className="mb-1 flex items-baseline justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400">{title}</p>
        <p className="text-xs text-zinc-500">
          {new Date(fromIso(picked)).toLocaleDateString(undefined, { dateStyle: "medium", timeZone: "UTC" })}
        </p>
      </div>
      <div className="mb-2 flex h-8 items-center justify-between">
        <NavButton label={`${title}: previous month`} onClick={() => onMonthChange(addMonths(month, -1))}>
          ‹
        </NavButton>
        <p className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          {new Date(fromIso(month)).toLocaleDateString(undefined, { month: "long", year: "numeric", timeZone: "UTC" })}
        </p>
        <NavButton
          label={`${title}: next month`}
          disabled={month >= monthOf(max)}
          onClick={() => onMonthChange(addMonths(month, 1))}
        >
          ›
        </NavButton>
      </div>
      <div className="grid grid-cols-7 gap-y-1 text-center">
        {WEEKDAYS.map((w) => (
          <span key={w} className="pb-1 text-xs font-medium text-zinc-400">
            {w}
          </span>
        ))}
        {monthDays(month).map((day, j) => {
          if (!day) return <span key={`blank-${j}`} />;
          const mark = day <= max ? markOf(day) : null;
          return (
            <button
              key={day}
              type="button"
              disabled={day > max}
              onClick={() => onPick(day)}
              aria-label={`${day}${mark ? ` (${MARK_STYLES[mark].label.toLowerCase()})` : ""}`}
              aria-pressed={day === picked}
              title={mark ? MARK_STYLES[mark].label : undefined}
              className={dayClass(day)}
            >
              {Number(day.slice(8))}
              {mark && (
                <span className={`absolute bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full ${MARK_STYLES[mark].dot}`} />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function NavButton({
  label,
  disabled,
  onClick,
  children,
}: {
  label: string;
  disabled?: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      disabled={disabled}
      onClick={onClick}
      className="flex h-8 w-8 items-center justify-center rounded-lg border border-zinc-300 text-lg leading-none text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-30 dark:border-zinc-700 dark:text-zinc-200 dark:hover:bg-zinc-800"
    >
      {children}
    </button>
  );
}
