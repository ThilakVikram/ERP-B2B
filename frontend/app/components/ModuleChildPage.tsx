import Link from "next/link";
import { getModuleChild } from "../modules";

/** Placeholder page for a module sub-route (e.g. /inventory/item) until it gets its own content. */
export function ModuleChildPage({ module: moduleSlug, slug }: { module: string; slug: string }) {
  const { module: m, child } = getModuleChild(moduleSlug, slug);
  return (
    <div className="flex-1">
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 lg:py-8">
        <Link href={`/${m.slug}`} className="text-sm text-zinc-500 hover:text-indigo-500">
          {m.name}
        </Link>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">{child.title}</h1>
        <div className="mt-8 rounded-2xl border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500 dark:border-zinc-700">
          Nothing here yet — {child.title.toLowerCase()} are coming soon.
        </div>
      </main>
    </div>
  );
}
