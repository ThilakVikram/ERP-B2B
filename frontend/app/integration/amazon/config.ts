// Everything the Amazon integration shows is driven from here.
// Add a region to REGIONS; add a section to SECTIONS together with its route folder
// (app/integration/amazon/<slug>/page.tsx). Sections and their tabs appear in the sidebar.

export type RegionCode = "NA" | "EU" | "FE";

export type Marketplace = {
  code: string;
  id: string; // Amazon marketplace ID
  name: string;
};

export type Region = {
  code: RegionCode;
  name: string;
  countries: string;
  marketplaces: Marketplace[];
};

// Marketplace IDs: https://developer-docs.amazon/sp-api/docs/marketplace-ids
export const REGIONS: Region[] = [
  {
    code: "NA",
    name: "North America",
    countries: "US · CA · MX · BR",
    marketplaces: [
      { code: "US", id: "ATVPDKIKX0DER", name: "United States" },
      { code: "CA", id: "A2EUQ1WTGCTBG2", name: "Canada" },
      { code: "MX", id: "A1AM78C64UM0Y8", name: "Mexico" },
      { code: "BR", id: "A2Q3Y263D00KWC", name: "Brazil" },
    ],
  },
  {
    code: "EU",
    name: "Europe",
    countries: "UK · DE · FR · IT · ES · IN · AE …",
    marketplaces: [
      { code: "UK", id: "A1F83G8C2ARO7P", name: "United Kingdom" },
      { code: "DE", id: "A1PA6795UKMFR9", name: "Germany" },
      { code: "FR", id: "A13V1IB3VIYZZH", name: "France" },
      { code: "IT", id: "APJ6JRA9NG5V4", name: "Italy" },
      { code: "ES", id: "A1RKKUPIHCS9HS", name: "Spain" },
      { code: "NL", id: "A1805IZSGTT6HS", name: "Netherlands" },
      { code: "SE", id: "A2NODRKZP88ZB9", name: "Sweden" },
      { code: "PL", id: "A1C3SOZRARQ6R3", name: "Poland" },
      { code: "BE", id: "AMEN7PMS3EDWL", name: "Belgium" },
      { code: "IE", id: "A28R8C7NBKEWEA", name: "Ireland" },
      { code: "TR", id: "A33AVAJ2PDY3EV", name: "Turkey" },
      { code: "AE", id: "A2VIGQ35RCS4UG", name: "UAE" },
      { code: "SA", id: "A17E79C6D8DWNP", name: "Saudi Arabia" },
      { code: "EG", id: "ARBP9OOSHTCHU", name: "Egypt" },
      { code: "IN", id: "A21TJRUUN4KGV", name: "India" },
      { code: "ZA", id: "AE08WJ6YKNBMC", name: "South Africa" },
    ],
  },
  {
    code: "FE",
    name: "Far East",
    countries: "JP · AU · SG",
    marketplaces: [
      { code: "JP", id: "A1VC38T7YXB528", name: "Japan" },
      { code: "AU", id: "A39IBJ37TRP1C6", name: "Australia" },
      { code: "SG", id: "A19VAU5U5O7RUS", name: "Singapore" },
    ],
  },
];

export type FeatureProps = { region: Region };

export type SectionTab = {
  slug: string; // route: /integration/amazon/<section>/<slug>
  title: string;
  subtitle: string;
};

export type SectionIcon = "store" | "box" | "report" | "database";

export type Section = {
  slug: string; // route: /integration/amazon/<slug>
  title: string;
  navTitle: string; // shorter label for the sidebar
  icon: SectionIcon;
  description: string;
  api: string;
  tabs?: SectionTab[]; // sub-routes, one per type
  indexTitle?: string; // sidebar entry for the section's own page, listed before its tabs
};

// One tab per report category (backend: integration/amazon/reports/<folder>/).
export const REPORT_TABS: SectionTab[] = [
  { slug: "orders", title: "Orders", subtitle: "All orders by order date" },
  { slug: "listings", title: "Listings", subtitle: "All listings" },
];

// Report types the Reports section queues (its request-history filter).
export const REPORT_TYPES = ["GET_FLAT_FILE_ALL_ORDERS_DATA_BY_ORDER_DATE_GENERAL", "GET_MERCHANT_LISTINGS_ALL_DATA"];

// One tab per Data Kiosk query (backend: integration/amazon/data_kiosk/<dataset>/).
export const DATA_KIOSK_TABS: SectionTab[] = [
  { slug: "economics", title: "SKU Economics", subtitle: "analytics_economics_2024_03_15" },
];

export const SECTIONS: Section[] = [
  {
    slug: "sellers",
    title: "Marketplace participations",
    navTitle: "Marketplaces",
    icon: "store",
    description:
      "Marketplaces this seller account can sell in, with participation and listing status.",
    api: "Sellers API v1",
  },
  {
    slug: "fba",
    title: "FBA inventory",
    navTitle: "FBA inventory",
    icon: "box",
    description:
      "Per-SKU FBA stock for a marketplace: fulfillable, inbound, reserved and unfulfillable units.",
    api: "FBA Inventory API v1",
  },
  {
    slug: "reports",
    title: "Reports",
    navTitle: "Reports",
    icon: "report",
    description:
      "Request Amazon order and listing reports and monitor them. Reports run one at a time, in the order they were requested.",
    api: "Reports API 2021-06-30",
    tabs: REPORT_TABS,
    indexTitle: "Overview",
  },
  {
    slug: "data_kiosk",
    title: "Data Kiosk",
    navTitle: "Data Kiosk",
    icon: "database",
    description:
      "Schedule Data Kiosk GraphQL queries (SKU Economics) over a date range and monitor them. They run one at a time in their own queue, separate from reports.",
    api: "Data Kiosk API 2023-11-15",
    tabs: DATA_KIOSK_TABS,
  },
];
