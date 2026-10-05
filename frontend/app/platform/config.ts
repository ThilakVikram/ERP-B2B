// Platforms under /platform: the app's own records per sales channel, built from the integration data.
// Add one here with its route folder (app/platform/<slug>/).

export type Platform = {
  slug: string; // route: /platform/<slug>
  name: string;
};

export const PLATFORMS: Platform[] = [{ slug: "amazon", name: "Amazon" }];
