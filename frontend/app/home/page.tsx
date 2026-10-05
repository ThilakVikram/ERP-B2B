import Link from "next/link";
import { Icon, type IconName } from "../components/shell/icons";
import { MODULES } from "../modules";

const SHORTCUTS: { href: string; name: string; description: string; icon: IconName }[] = [
  ...MODULES.map((m) => ({ href: `/${m.slug}`, name: m.name, description: m.description, icon: m.icon })),
  { href: "/integration", name: "Integrations", description: "Connected services that sync data into iTrend.", icon: "plug" },
  { href: "/platform", name: "Platform", description: "The app's own records per sales channel.", icon: "grid" },
];

export default function HomePage() {
  return (
    <div className="flex-1">
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-8 lg:py-8">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">Home</h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">Jump into any part of iTrend.</p>

        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SHORTCUTS.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="group rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-400 hover:shadow-lg dark:border-zinc-800 dark:bg-zinc-900 dark:shadow-black/20 dark:hover:border-indigo-500"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-300">
                <Icon name={s.icon} />
              </span>
              <p className="mt-4 font-semibold text-zinc-900 group-hover:text-indigo-600 dark:text-zinc-50 dark:group-hover:text-indigo-400">
                {s.name}
              </p>
              <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{s.description}</p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
