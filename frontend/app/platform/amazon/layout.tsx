"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SECTIONS } from "./config";

// Section routes live in the sidebar; this frame shows where you are.
export default function PlatformAmazonLayout({ children }: LayoutProps<"/platform/amazon">) {
  const pathname = usePathname();
  const section = SECTIONS.find((s) => pathname.startsWith(`/platform/amazon/${s.slug}`));

  return (
    <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-8 lg:py-8">
      <header className="relative mb-8 overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-lg shadow-black/20 sm:p-7">
        <div className="pointer-events-none absolute -right-20 -top-24 h-64 w-64 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-28 right-1/3 h-56 w-56 rounded-full bg-violet-600/15 blur-3xl" />

        <div className="relative min-w-0">
          <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1.5 text-xs font-medium text-zinc-500">
            <span>Platform</span>
            <span>/</span>
            <Link href="/platform/amazon" className="hover:text-indigo-400">Amazon</Link>
            {section && (
              <>
                <span>/</span>
                <span className="text-zinc-300">{section.title}</span>
              </>
            )}
          </nav>
          <div className="mt-2 flex flex-wrap items-center gap-2.5">
            <h1 className="text-2xl font-semibold tracking-tight text-white">{section?.title ?? "Amazon"}</h1>
            {section && (
              <span className="rounded-full border border-indigo-500/30 bg-indigo-500/10 px-2.5 py-0.5 font-mono text-xs font-medium text-indigo-300">
                from {section.source}
              </span>
            )}
          </div>
          {section && <p className="mt-2 max-w-2xl text-sm text-zinc-400">{section.description}</p>}
        </div>
      </header>

      <section>{children}</section>
    </main>
  );
}
