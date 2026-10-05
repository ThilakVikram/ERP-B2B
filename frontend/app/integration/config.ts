// Integrations listed on /integration. Add one here with its route folder (app/integration/<slug>/).

export type Integration = {
  slug: string; // route: /integration/<slug>
  name: string;
  description: string;
  services: string[];
};

export const INTEGRATIONS: Integration[] = [
  {
    slug: "amazon",
    name: "Amazon Selling Partner",
    description: "Seller account, FBA inventory and reports from Amazon SP-API.",
    services: ["Sellers", "FBA inventory", "Reports"],
  },
];
