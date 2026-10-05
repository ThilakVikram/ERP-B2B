"use client";

// Signed-in frame: a sidebar with every route (collapsible on desktop, a drawer on mobile) next to the page.

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import type { User } from "../../lib/auth";
import { Icon } from "./icons";
import { NAV, filterNodes, isActive, type NavNode } from "./nav";

const COLLAPSED_KEY = "itrend.sidebar.collapsed";

function readCollapsed() {
  try {
    return localStorage.getItem(COLLAPSED_KEY) === "1";
  } catch {
    return false;
  }
}

export function AppShell({
  user,
  onLogout,
  children,
}: {
  user: User;
  onLogout: () => void;
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  // Only mounted on the client (AuthGuard renders it after /me), so reading storage here is safe.
  const [collapsed, setCollapsed] = useState(readCollapsed);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const searchRef = useRef<HTMLInputElement>(null);

  function toggleCollapsed() {
    const next = !collapsed;
    setCollapsed(next);
    try {
      localStorage.setItem(COLLAPSED_KEY, next ? "1" : "0");
    } catch {}
  }

  function focusSearch() {
    setCollapsed(false);
    setMobileOpen(true);
    requestAnimationFrame(() => searchRef.current?.focus());
  }

  // Ctrl/⌘ + K jumps to the page search.
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCollapsed(false);
        setMobileOpen(true);
        requestAnimationFrame(() => searchRef.current?.focus());
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const q = query.trim().toLowerCase();
  const groups = NAV.map((g) => ({ ...g, items: filterNodes(g.items, q) })).filter((g) => g.items.length > 0);

  const initials = `${user.firstName[0] ?? ""}${user.lastName[0] ?? ""}`.toUpperCase() || "?";
  const wide = collapsed ? "lg:hidden" : ""; // parts shown only in the full-width sidebar
  const closeMobile = () => setMobileOpen(false);

  return (
    <div className="flex min-h-screen flex-1">
      {mobileOpen && (
        <div className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden" onClick={closeMobile} aria-hidden="true" />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-zinc-800 bg-sidebar transition-[width,translate] duration-200 lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } ${collapsed ? "lg:w-20" : "lg:w-72"}`}
        aria-label="Sidebar"
      >
        {/* Brand */}
        <div className={`flex h-16 shrink-0 items-center px-5 ${collapsed ? "justify-between lg:justify-center lg:px-0" : "justify-between"}`}>
          <Link href="/home" onClick={closeMobile} className="flex items-center gap-2.5 text-lg font-semibold text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-400 to-violet-600 text-white shadow-lg shadow-indigo-900/40">
              i
            </span>
            <span className={wide}>iTrend</span>
          </Link>
          <button
            type="button"
            onClick={toggleCollapsed}
            className={`hidden rounded-lg p-1.5 text-zinc-400 transition hover:bg-zinc-800 hover:text-white lg:block ${wide}`}
            aria-label="Collapse sidebar"
            title="Collapse sidebar"
          >
            <Icon name="collapse" className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={closeMobile}
            className="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white lg:hidden"
            aria-label="Close menu"
          >
            <Icon name="close" className="h-5 w-5" />
          </button>
        </div>

        {/* Profile */}
        <div className={`flex items-center gap-3 px-5 pb-4 pt-2 ${collapsed ? "lg:justify-center lg:px-0" : ""}`}>
          <span
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-400 to-violet-500 p-0.5"
            title={collapsed ? `${user.firstName} ${user.lastName}` : undefined}
          >
            <span className="flex h-full w-full items-center justify-center rounded-full bg-zinc-900 text-sm font-semibold text-white">
              {initials}
            </span>
          </span>
          <div className={`min-w-0 ${wide}`}>
            <p className="truncate text-sm font-medium text-white">
              {user.firstName} {user.lastName}
            </p>
            <p className="truncate text-xs text-zinc-500">{user.email}</p>
          </div>
        </div>

        {/* Search */}
        <div className="px-4 pb-2">
          {collapsed && (
            <button
              type="button"
              onClick={focusSearch}
              className="hidden w-full items-center justify-center rounded-lg py-2.5 text-zinc-400 transition hover:bg-zinc-800 hover:text-white lg:flex"
              aria-label="Search pages"
              title="Search pages (Ctrl K)"
            >
              <Icon name="search" />
            </button>
          )}
          <label className={`relative block ${wide}`}>
            <span className="sr-only">Search pages</span>
            <Icon name="search" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500" />
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Escape" && setQuery("")}
              placeholder="Search pages…"
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950/60 py-2 pl-9 pr-12 text-sm text-zinc-100 placeholder:text-zinc-500 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
            />
            <kbd className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded border border-zinc-700 px-1.5 text-[10px] font-medium text-zinc-500">
              Ctrl K
            </kbd>
          </label>
        </div>

        {/* Routes */}
        <nav className="flex-1 overflow-y-auto py-2">
          {groups.map((g) => (
            <div key={g.label} className="mb-4">
              <p className={`px-6 pb-2 pt-3 text-[11px] font-medium uppercase tracking-wider text-zinc-500 ${wide}`}>
                {g.label}
              </p>
              {collapsed && <div className="mx-5 my-2 hidden border-t border-zinc-800 lg:block" />}
              {g.items.map((item) => (
                <NavEntry
                  key={item.href}
                  node={item}
                  depth={0}
                  pathname={pathname}
                  collapsed={collapsed}
                  forceOpen={!!q}
                  expanded={expanded}
                  onToggle={(href, open) => setExpanded((e) => ({ ...e, [href]: open }))}
                  onExpandSidebar={() => setCollapsed(false)}
                  onNavigate={closeMobile}
                />
              ))}
            </div>
          ))}
          {groups.length === 0 && <p className="px-6 text-sm text-zinc-500">No pages match “{query}”.</p>}
        </nav>

        {/* Footer */}
        <div className="border-t border-zinc-800 p-3">
          <button
            type="button"
            onClick={onLogout}
            title="Log out"
            className={`flex w-full items-center gap-4 rounded-lg px-3 py-2.5 text-sm font-medium text-zinc-400 transition hover:bg-rose-500/10 hover:text-rose-400 ${
              collapsed ? "lg:justify-center" : ""
            }`}
          >
            <Icon name="logout" />
            <span className={wide}>Log out</span>
          </button>
        </div>
      </aside>

      <div className={`flex min-w-0 flex-1 flex-col transition-[padding] duration-200 ${collapsed ? "lg:pl-20" : "lg:pl-72"}`}>
        {/* Mobile top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-zinc-800 bg-sidebar/90 px-4 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-1.5 text-zinc-300 hover:bg-zinc-800"
            aria-label="Open menu"
          >
            <Icon name="menu" />
          </button>
          <span className="font-semibold text-white">iTrend</span>
        </header>

        {/* Expand button for the collapsed desktop sidebar */}
        {collapsed && (
          <button
            type="button"
            onClick={toggleCollapsed}
            className="fixed left-[4.25rem] top-5 z-50 hidden h-6 w-6 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900 text-zinc-300 shadow transition hover:bg-indigo-600 hover:text-white lg:flex"
            aria-label="Expand sidebar"
            title="Expand sidebar"
          >
            <Icon name="chevron" className="h-3.5 w-3.5" />
          </button>
        )}

        {children}
      </div>
    </div>
  );
}

type NavEntryProps = {
  node: NavNode;
  depth: number; // 0: top-level item with an icon; deeper levels are indented sub-routes
  pathname: string;
  collapsed: boolean;
  forceOpen: boolean; // searching: show every match
  expanded: Record<string, boolean>; // groups the user opened/closed, by href
  onToggle: (href: string, open: boolean) => void;
  onExpandSidebar: () => void;
  onNavigate: () => void;
};

function containsActive(pathname: string, node: NavNode): boolean {
  return isActive(pathname, node) || !!node.children?.some((c) => containsActive(pathname, c));
}

function NavEntry(props: NavEntryProps) {
  const { node, depth, pathname, collapsed, forceOpen, expanded, onToggle, onExpandSidebar, onNavigate } = props;
  const active = containsActive(pathname, node);
  const current = !node.children?.length && isActive(pathname, node);
  const hasChildren = !!node.children?.length;
  const open = forceOpen || (expanded[node.href] ?? active);
  const top = depth === 0;

  // In the collapsed desktop sidebar only top-level icons show; sub-routes hide.
  const hideCollapsed = collapsed ? "lg:hidden" : "";

  const row = top
    ? `group relative flex w-full items-center gap-4 px-6 py-3 text-[15px] transition ${
        active ? "text-white" : "text-zinc-300 hover:bg-zinc-800/40 hover:text-white"
      } ${collapsed ? "lg:justify-center lg:px-0" : ""}`
    : `group flex w-full items-center gap-3 py-2 pr-6 text-sm transition ${
        current ? "font-semibold text-white" : active ? "text-zinc-100" : "text-zinc-400 hover:text-white"
      }`;
  const indent = top ? undefined : { paddingLeft: `${2.1 + depth * 1.25}rem` };

  const marker = top ? (
    <span className={active ? "text-indigo-400" : "text-zinc-400 group-hover:text-zinc-200"}>
      <Icon name={node.icon ?? "grid"} />
    </span>
  ) : node.icon ? (
    <span className={active ? "text-indigo-400" : "text-zinc-500 group-hover:text-zinc-300"}>
      <Icon name={node.icon} className="h-4 w-4" />
    </span>
  ) : (
    <span
      className={`h-2 w-2 shrink-0 rounded-full border-2 ${
        current ? "border-indigo-400 bg-white" : active ? "border-indigo-400" : "border-zinc-500"
      }`}
      aria-hidden="true"
    />
  );
  const label = <span className={`min-w-0 flex-1 truncate text-left ${top ? hideCollapsed : ""}`}>{node.title}</span>;

  const body = hasChildren ? (
    <>
      <button
        type="button"
        onClick={() => {
          // A collapsed sidebar has no room for sub-routes: widen it and open this group.
          if (collapsed && top) {
            onExpandSidebar();
            onToggle(node.href, true);
          } else onToggle(node.href, !open);
        }}
        aria-expanded={open}
        title={collapsed && top ? node.title : undefined}
        className={row}
        style={indent}
      >
        {marker}
        {label}
        <Icon
          name="chevron"
          className={`h-4 w-4 shrink-0 text-zinc-500 transition-transform ${open ? "rotate-90" : ""} ${top ? hideCollapsed : ""}`}
        />
      </button>
      {open && (
        <ul className={`${top ? "pb-2" : ""} ${hideCollapsed}`}>
          {node.children!.map((c) => (
            <li key={c.href + (c.exact ? ":exact" : "")}>
              <NavEntry {...props} node={c} depth={depth + 1} />
            </li>
          ))}
        </ul>
      )}
    </>
  ) : (
    <Link
      href={node.href}
      onClick={onNavigate}
      aria-current={current ? "page" : undefined}
      title={collapsed && top ? node.title : undefined}
      className={row}
      style={indent}
    >
      {marker}
      {label}
    </Link>
  );

  if (!top) return body;
  return (
    <div className={`relative ${active ? "bg-gradient-to-r from-indigo-500/15 to-transparent" : ""}`}>
      {active && <span className="absolute inset-y-0 left-0 w-1 rounded-r bg-indigo-500" aria-hidden="true" />}
      {body}
    </div>
  );
}
