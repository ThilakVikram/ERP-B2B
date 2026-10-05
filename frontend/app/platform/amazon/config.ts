// Sections of /platform/amazon. Add one here together with its route folder
// (app/platform/amazon/<slug>/page.tsx); sections appear in the sidebar.

import type { SectionIcon } from "../../integration/amazon/config";

export type PlatformSection = {
  slug: string; // route: /platform/amazon/<slug>
  title: string;
  icon: SectionIcon;
  description: string;
  source: string; // integration table it syncs from
};

export const SECTIONS: PlatformSection[] = [
  {
    slug: "marketplaces",
    title: "Marketplaces",
    icon: "store",
    description:
      "Marketplaces the app sells in. Sync creates or updates them from the stored marketplace participations.",
    source: "amazon_intg_marketplace_participations",
  },
  {
    slug: "items",
    title: "Items",
    icon: "box",
    description:
      "Items (SKUs) per marketplace. Sync creates or updates them from the stored listings report rows; sync marketplaces first.",
    source: "amazon_intg_merchant_listings",
  },
];
