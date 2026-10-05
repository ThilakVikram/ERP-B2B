export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-1 bg-zinc-50 dark:bg-zinc-950">
      <aside className="relative hidden w-1/2 flex-col justify-between overflow-hidden bg-indigo-600 p-12 text-white lg:flex">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-indigo-500/60 blur-3xl" />
        <div className="absolute -bottom-32 -left-16 h-96 w-96 rounded-full bg-violet-500/50 blur-3xl" />

        <div className="relative flex items-center gap-2 text-xl font-semibold">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white text-indigo-600">
            i
          </span>
          iTrend
        </div>

        <div className="relative max-w-md">
          <h2 className="text-4xl font-semibold leading-tight">
            Automate your workflow, stay ahead of the trend.
          </h2>
          <p className="mt-4 text-indigo-100">
            Sign in to manage your automations, track results and collaborate
            with your team — all in one place.
          </p>
        </div>

        <p className="relative text-sm text-indigo-200">
          © {new Date().getFullYear()} iTrend Solution. All rights reserved.
        </p>
      </aside>

      <main className="flex flex-1 items-center justify-center px-4 py-12 sm:px-8">
        <div className="w-full max-w-md">{children}</div>
      </main>
    </div>
  );
}
