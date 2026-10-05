// Backend calls for the Amazon platform records (marketplaces, items).

import { apiFetch } from "../../lib/api";
import type { RegionCode } from "../../integration/amazon/config";

export type AmazonMarketplace = {
  id: number;
  integrationId: number | null;
  region: RegionCode;
  marketplaceId: string;
  name: string;
  countryCode: string;
  currencyCode: string;
  languageCode: string;
  domainName: string;
  storeName: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
};

// normal: only integration rows not linked yet; full: every row (refreshes links and fields). Neither deletes.
export type SyncMode = "normal" | "full";

export type AmazonMarketplaceSync = {
  mode: SyncMode;
  created: number;
  updated: number;
  marketplaces: AmazonMarketplace[];
};

export type AmazonItem = {
  id: number;
  amazonMarketplaceId: number;
  integrationId: number | null;
  marketplace: { id: number; region: RegionCode; marketplaceId: string; name: string; countryCode: string };
  sellerSku: string;
  asin: string | null;
  fnSku: string | null;
  title: string | null;
  itemCondition: string | null;
  fulfillmentChannel: string | null;
  price: string | null; // Decimal, serialized as a string
  currencyCode: string | null;
  imageUrl: string | null;
  status: string | null;
  createdAt: string;
  updatedAt: string;
};

export type AmazonItemPage = { total: number; items: AmazonItem[] };

export type AmazonItemSync = { mode: SyncMode; created: number; updated: number; skipped: number };

const regionQuery = (region: RegionCode | null) => (region ? `?region=${region}` : "");

function syncQuery(region: RegionCode | null, mode: SyncMode) {
  const query = new URLSearchParams({ mode });
  if (region) query.set("region", region);
  return `?${query}`;
}

export function listAmazonMarketplaces(region: RegionCode | null) {
  return apiFetch<AmazonMarketplace[]>(`/api/v1/platform/amazon/marketplaces${regionQuery(region)}`);
}

export function syncAmazonMarketplaces(region: RegionCode | null, mode: SyncMode) {
  return apiFetch<AmazonMarketplaceSync>(`/api/v1/platform/amazon/marketplaces/sync${syncQuery(region, mode)}`, {
    method: "POST",
  });
}

export function listAmazonItems(params: {
  region: RegionCode | null;
  amazonMarketplaceId: number | null;
  q: string;
  limit: number;
  offset: number;
}) {
  const query = new URLSearchParams({ limit: String(params.limit), offset: String(params.offset) });
  if (params.region) query.set("region", params.region);
  if (params.amazonMarketplaceId) query.set("amazonMarketplaceId", String(params.amazonMarketplaceId));
  if (params.q) query.set("q", params.q);
  return apiFetch<AmazonItemPage>(`/api/v1/platform/amazon/items?${query}`);
}

export function syncAmazonItems(region: RegionCode | null, mode: SyncMode) {
  return apiFetch<AmazonItemSync>(`/api/v1/platform/amazon/items/sync${syncQuery(region, mode)}`, { method: "POST" });
}
