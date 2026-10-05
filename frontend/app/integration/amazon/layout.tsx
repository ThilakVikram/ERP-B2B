"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { REGIONS, SECTIONS } from "./config";
import { RegionProvider, useRegion } from "./region";

export default function AmazonIntegrationLayout({ children }: LayoutProps<"/integration/amazon">) {
  return (
    <RegionProvider>
      <AmazonShell>{children}</AmazonShell>
    </RegionProvider>
  );
}

// Section routes live in the sidebar; this frame shows where you are and the region to sync.
function AmazonShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const section = SECTIONS.find((s) => pathname.startsWith(`/integration/amazon/${s.slug}`));
  const tab = section?.tabs?.find((t) => pathname.startsWith(`/integration/amazon/${section.slug}/${t.slug}`));

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-8 lg:py-8">
      <header className="relative mb-8 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-lg shadow-black/20 sm:p-7">
        <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 right-1/3 h-56 w-56 rounded-full bg-violet-600/15 blur-3xl" />

        <div className="relative flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div className="min-w-0">
            <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1.5 text-xs font-medium text-zinc-500">
              <Link href="/integration" className="hover:text-indigo-400">Integrations</Link>
              <span>/</span>
              <span>Amazon</span>
              {section && (
                <>
                  <span>/</span>
                  <span className={tab ? "" : "text-zinc-300"}>{section.navTitle}</span>
                </>
              )}
              {tab && (
                <>
                  <span>/</span>
                  <span className="text-zinc-300">{tab.title}</span>
                </>
              )}
            </nav>
            <div className="mt-2 flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl font-semibold tracking-tight text-white">
                {section ? (tab ? `${section.title} · ${tab.title}` : section.title) : "Amazon Selling Partner"}
              </h1>
              {section && (
                <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 text-xs font-medium text-indigo-300">
                  {section.api}
                </span>
              )}
            </div>
            {section && <p className="mt-2 max-w-2xl text-sm text-zinc-400">{section.description}</p>}
            {tab && <p className="mt-1 font-mono text-xs text-zinc-500">{tab.subtitle}</p>}
          </div>

          <RegionSwitcher />
        </div>
      </header>

      <section>{children}</section>
    </main>
  );
}

function RegionSwitcher() {
  const { region, setRegionCode } = useRegion();
  return (
    <div className="shrink-0">
      <p className="mb-2 text-[11px] font-medium uppercase tracking-wider text-zinc-500">Region</p>
      <div className="grid grid-cols-3 gap-1 rounded-xl border border-zinc-800 bg-zinc-950/70 p-1" role="radiogroup" aria-label="Region">
        {REGIONS.map((r) => {
          const active = r.code === region.code;
          return (
            <button
              key={r.code}
              type="button"
              role="radio"
              aria-checked={active}
              onClick={() => setRegionCode(r.code)}
              title={r.countries}
              className={`rounded-lg px-4 py-2 text-left transition ${
                active
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-900/40"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
              }`}
            >
              <span className="block text-sm font-semibold">{r.code}</span>
              <span className={`block whitespace-nowrap text-[11px] ${active ? "text-indigo-100" : "text-zinc-500"}`}>
                {r.name}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
