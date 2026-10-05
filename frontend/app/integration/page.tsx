import Link from "next/link";
import { INTEGRATIONS } from "./config";

export default function IntegrationsPage() {
  return (
    <div className="flex-1">
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 lg:py-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
          Integrations
        </h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Connected services that sync data into iTrend.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {INTEGRATIONS.map((i) => (
            <Link
              key={i.slug}
              href={`/integration/${i.slug}`}
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-400 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-black/20 dark:hover:border-indigo-500"
            >
              <p className="font-semibold text-zinc-900 group-hover:text-indigo-600 dark:text-zinc-50 dark:group-hover:text-indigo-400">
                {i.name}
              </p>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{i.description}</p>
              <div className="mt-4 flex flex-wrap gap-1.5">
                {i.services.map((s) => (
                  <span
                    key={s}
                    className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
                  >
                    {s}
                  </span>
                ))}
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
