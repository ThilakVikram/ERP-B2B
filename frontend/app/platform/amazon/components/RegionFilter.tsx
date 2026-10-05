"use client";

import { REGIONS, type RegionCode } from "../../../integration/amazon/config";

/** All regions (null) or one. */
export function RegionFilter({ value, onChange }: { value: RegionCode | null; onChange: (v: RegionCode | null) => void }) {
  const options: { code: RegionCode | null; label: string; title: string }[] = [
    { code: null, label: "All", title: "All regions" },
    ...REGIONS.map((r) => ({ code: r.code, label: r.code, title: r.name })),
  ];
  return (
    <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Region">
      {options.map((o) => {
        const active = o.code === value;
        return (
          <button
            key={o.label}
            type="button"
            role="radio"
            aria-checked={active}
            title={o.title}
            onClick={() => onChange(o.code)}
            className={`rounded-full border px-3.5 py-1.5 text-sm font-medium transition ${
              active
                ? "border-indigo-600 bg-indigo-600 text-white shadow-sm"
                : "border-zinc-300 bg-white text-zinc-700 hover:border-indigo-400 hover:text-indigo-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300"
            }`}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
