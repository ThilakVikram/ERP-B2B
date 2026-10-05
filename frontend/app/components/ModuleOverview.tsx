import Link from "next/link";
import { getModule } from "../modules";

/** Landing page of a module (/inventory, /sales, /purchase): its sub-routes, or a placeholder until it has some. */
export function ModuleOverview({ slug }: { slug: string }) {
  const m = getModule(slug);
  return (
    <div className="flex-1">
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 lg:py-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">{m.name}</h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{m.description}</p>

        {m.children.length > 0 ? (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {m.children.map((c) => (
              <Link
                key={c.slug}
                href={`/${m.slug}/${c.slug}`}
                className="rounded-2xl border border-zinc-200 bg-white p-6 font-semibold text-zinc-900 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-400 hover:text-indigo-600 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:text-zinc-50 dark:shadow-black/20 dark:hover:border-indigo-500 dark:hover:text-indigo-400"
              >
                {c.title}
              </Link>
            ))}
          </div>
        ) : (
          <div className="mt-8 rounded-2xl border border-dashed border-zinc-300 p-10 text-center text-sm text-zinc-500 dark:border-zinc-700">
            Nothing here yet — {m.name.toLowerCase()} pages are coming soon.
          </div>
        )}
      </main>
    </div>
  );
}
