// Business modules: /inventory, /sales and /purchase. Each has its route folder (app/<slug>/) and shows up
// on /home and in the sidebar. Add sub-routes to a module's `children` together with their route folders
// (app/<slug>/<child>/page.tsx).

import type { IconName } from "./components/shell/icons";

export type ModuleChild = {
  slug: string; // route: /<module>/<slug>
  title: string;
};

export type AppModule = {
  slug: string; // route: /<slug>
  name: string;
  description: string;
  icon: IconName;
  children: ModuleChild[];
};

export const MODULES: AppModule[] = [
  {
    slug: "inventory",
    name: "Inventory",
    description: "Stock levels and movements across warehouses and marketplaces.",
    icon: "box",
    children: [
      { slug: "item", title: "Items" },
      { slug: "warehouse", title: "Warehouses" },
    ],
  },
  {
    slug: "sales",
    name: "Sales",
    description: "Orders, revenue and returns from every sales channel.",
    icon: "cart",
    children: [],
  },
  {
    slug: "purchase",
    name: "Purchase",
    description: "Suppliers, purchase orders and inbound shipments.",
    icon: "truck",
    children: [
      { slug: "purchase_order", title: "Purchase Orders" },
      { slug: "purchase_advance", title: "Purchase Advances" },
      { slug: "purchase_balance", title: "Purchase Balances" },
      { slug: "purchase_receive", title: "Purchase Receives" },
      { slug: "purchase_bill", title: "Purchase Bills" },
    ],
  },
];

export function getModule(slug: string): AppModule {
  const m = MODULES.find((m) => m.slug === slug);
  if (!m) throw new Error(`Unknown module: ${slug}`);
  return m;
}

export function getModuleChild(moduleSlug: string, slug: string): { module: AppModule; child: ModuleChild } {
  const m = getModule(moduleSlug);
  const child = m.children.find((c) => c.slug === slug);
  if (!child) throw new Error(`Unknown ${moduleSlug} sub-route: ${slug}`);
  return { module: m, child };
}
