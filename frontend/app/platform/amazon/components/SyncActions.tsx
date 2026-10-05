"use client";

import { SyncButton } from "../../../integration/amazon/components/shared";
import type { SyncMode } from "../api";

/** Normal sync (only integration rows not linked yet) and full sync (every row, refreshing links and fields). */
export function SyncActions({
  syncing,
  onSync,
  scope,
}: {
  syncing: SyncMode | null;
  onSync: (mode: SyncMode) => void;
  scope: string; // e.g. "NA" or "all regions"
}) {
  return (
    <div className="flex flex-col items-stretch gap-1.5 sm:items-end">
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => onSync("full")}
          disabled={syncing !== null}
          title="Re-sync every integration row: refreshes the fields and links of records already created. Nothing is deleted."
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2.5 text-sm font-semibold text-zinc-700 shadow-sm transition hover:border-indigo-400 hover:text-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200"
        >
          {syncing === "full" ? "Full syncing…" : "Full sync"}
        </button>
        <SyncButton
          onClick={() => onSync("normal")}
          syncing={syncing === "normal"}
          label={`Sync ${scope}`}
        />
      </div>
      <p className="text-xs text-zinc-500 dark:text-zinc-400">
        Sync: only rows not linked yet · Full sync: every row · Nothing is deleted
      </p>
    </div>
  );
}
