// Sidebar navigation, built from the module, integration and platform configs so a new module, sub-route,
// integration, platform, section or tab shows up automatically: Home, <module> → <sub-route>,
// Integrations → <integration> → <section> → <tab>, Platform → <platform> → <section>.

import { MODULES } from "../../modules";
import { INTEGRATIONS } from "../../integration/config";
import { SECTIONS as AMAZON_SECTIONS, type Section } from "../../integration/amazon/config";
import { PLATFORMS } from "../../platform/config";
import { SECTIONS as PLATFORM_AMAZON_SECTIONS, type PlatformSection } from "../../platform/amazon/config";
import type { IconName } from "./icons";

export type NavNode = {
  href: string;
  title: string;
  icon?: IconName;
  exact?: boolean; // active only on this exact path (its sub-paths belong to sibling items)
  children?: NavNode[];
};
export type NavGroup = { label: string; items: NavNode[] };

// Section routes per integration slug; an integration without sections links straight to its page.
const INTEGRATION_SECTIONS: Record<string, Section[]> = { amazon: AMAZON_SECTIONS };

function integrationNode(slug: string, title: string): NavNode {
  const base = `/integration/${slug}`;
  const sections = INTEGRATION_SECTIONS[slug];
  return {
    href: base,
    title,
    children: sections?.map((s) => ({
      href: `${base}/${s.slug}`,
      title: s.navTitle,
      icon: s.icon,
      children: s.tabs && [
        ...(s.indexTitle ? [{ href: `${base}/${s.slug}`, title: s.indexTitle, exact: true }] : []),
        ...s.tabs.map((t) => ({ href: `${base}/${s.slug}/${t.slug}`, title: t.title })),
      ],
    })),
  };
}

// Section routes per platform slug.
const PLATFORM_SECTIONS: Record<string, PlatformSection[]> = { amazon: PLATFORM_AMAZON_SECTIONS };

function platformNode(slug: string, title: string): NavNode {
  const base = `/platform/${slug}`;
  return {
    href: base,
    title,
    children: PLATFORM_SECTIONS[slug]?.map((s) => ({ href: `${base}/${s.slug}`, title: s.title, icon: s.icon })),
  };
}

export const NAV: NavGroup[] = [
  {
    label: "Main",
    items: [
      { href: "/home", title: "Home", icon: "home" },
      // A module without sub-routes links straight to its page.
      ...MODULES.map((m) => ({
        href: `/${m.slug}`,
        title: m.name,
        icon: m.icon,
        children: m.children.length
          ? [
              { href: `/${m.slug}`, title: "Overview", exact: true },
              ...m.children.map((c) => ({ href: `/${m.slug}/${c.slug}`, title: c.title })),
            ]
          : undefined,
      })),
      {
        href: "/integration",
        title: "Integrations",
        icon: "plug",
        children: [
          { href: "/integration", title: "Overview", exact: true },
          ...INTEGRATIONS.map((i) => integrationNode(i.slug, i.name)),
        ],
      },
      {
        href: "/platform",
        title: "Platform",
        icon: "grid",
        children: PLATFORMS.map((p) => platformNode(p.slug, p.name)),
      },
    ],
  },
];

export function isActive(pathname: string, node: NavNode): boolean {
  if (node.exact) return pathname === node.href;
  return pathname === node.href || pathname.startsWith(`${node.href}/`);
}

/** Nodes whose title (or a descendant's) matches `q`, keeping the tree shape; everything when `q` is empty. */
export function filterNodes(nodes: NavNode[], q: string): NavNode[] {
  if (!q) return nodes;
  return nodes.flatMap((n) => {
    if (n.title.toLowerCase().includes(q)) return [n];
    const children = filterNodes(n.children ?? [], q);
    return children.length ? [{ ...n, children }] : [];
  });
}
