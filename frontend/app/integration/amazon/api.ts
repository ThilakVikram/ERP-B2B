// Backend calls for the Amazon SP-API integration (sellers, inventory, reports, Data Kiosk).

import { apiFetch } from "../../lib/api";
import type { RegionCode } from "./config";

export type MarketplaceParticipation = {
  id: number;
  region: RegionCode;
  marketplaceId: string;
  name: string;
  countryCode: string;
  defaultCurrencyCode: string;
  defaultLanguageCode: string;
  domainName: string;
  storeName: string | null;
  isParticipating: boolean;
  hasSuspendedListings: boolean;
  lastSyncedAt: string;
  updatedAt: string;
};

export type MarketplaceParticipationSync = {
  region: RegionCode;
  count: number;
  participations: MarketplaceParticipation[];
};

export function listMarketplaceParticipations(region?: RegionCode) {
  const query = region ? `?region=${region}` : "";
  return apiFetch<MarketplaceParticipation[]>(
    `/api/v1/sellers/marketplace-participations${query}`,
  );
}

export function syncMarketplaceParticipations(region: RegionCode) {
  return apiFetch<MarketplaceParticipationSync>(
    `/api/v1/sellers/${region}/sync`,
    { method: "POST" },
  );
}

export type FbaInventorySummary = {
  id: number;
  region: RegionCode;
  marketplaceId: string;
  sellerSku: string;
  asin: string | null;
  fnSku: string | null;
  condition: string | null;
  productName: string | null;
  totalQuantity: number;
  stores: string[] | null;
  lastUpdatedTime: string | null;
  fulfillableQuantity: number;
  inboundWorkingQuantity: number;
  inboundShippedQuantity: number;
  inboundReceivingQuantity: number;
  totalReservedQuantity: number;
  pendingCustomerOrderQuantity: number;
  pendingTransshipmentQuantity: number;
  fcProcessingQuantity: number;
  totalResearchingQuantity: number;
  researchingQuantityBreakdown: { name: string | null; quantity: number | null }[] | null;
  totalUnfulfillableQuantity: number;
  customerDamagedQuantity: number;
  warehouseDamagedQuantity: number;
  distributorDamagedQuantity: number;
  carrierDamagedQuantity: number;
  defectiveQuantity: number;
  expiredQuantity: number;
  lastSyncedAt: string;
  updatedAt: string;
};

export type FbaInventorySync = {
  region: RegionCode;
  marketplaceId: string;
  count: number;
  syncedAt: string;
};

export function listInventorySummaries(marketplaceId: string) {
  return apiFetch<FbaInventorySummary[]>(
    `/api/v1/inventory/summaries?marketplaceId=${encodeURIComponent(marketplaceId)}`,
  );
}

export function syncInventorySummaries(marketplaceId: string) {
  return apiFetch<FbaInventorySync>(
    `/api/v1/inventory/${encodeURIComponent(marketplaceId)}/sync`,
    { method: "POST" },
  );
}

// ---------- Reports (/api/v1/reports/...) ----------

export type ReportSyncStatus = "QUEUED" | "PROCESSING" | "SYNCED" | "FAILED" | "CANCELLED";

export type AmazonReport = {
  id: number;
  reportId: string | null; // Amazon reportId, once requested
  reportType: string;
  region: RegionCode;
  marketplaceId: string;
  dataStartTime: string;
  dataEndTime: string;
  processingStatus: string | null; // Amazon's status
  syncStatus: ReportSyncStatus;
  rowCount: number;
  insertedCount: number;
  skippedCount: number;
  error: string | null;
  requestedById: number | null;
  startedAt: string | null;
  completedAt: string | null;
  createdAt: string;
  updatedAt: string;
  queuePosition: number | null; // 1 = next to run; only while QUEUED
};

export type ReportQueue = {
  current: AmazonReport | null;
  pending: AmazonReport[];
  counts: Record<ReportSyncStatus, number>; // every request ever queued, by status
};

export function getReportQueue() {
  return apiFetch<ReportQueue>("/api/v1/reports/queue");
}

export function cancelReport(id: number) {
  return apiFetch<AmazonReport>(`/api/v1/reports/${id}/cancel`, { method: "POST" });
}

// Marketplaces reports can be requested for: the seller's participating Amazon marketplaces
// (from the last Sellers sync). Omit region for all regions.
export function listReportMarketplaces(region?: RegionCode) {
  const query = region ? `?region=${region}` : "";
  return apiFetch<MarketplaceParticipation[]>(`/api/v1/reports/marketplaces${query}`);
}

export type ReportBatch = {
  queued: AmazonReport[];
  skipped: { startDate: string; endDate: string; reason: string }[]; // already queued or processing
};

// Queues the period as consecutive reports of `partitionDays` days (1-30); the last may be shorter.
export type ScheduleRequest = {
  marketplaceId: string;
  startDate: string; // YYYY-MM-DD
  endDate: string; // inclusive
  partitionDays: number;
};

export function scheduleOrderReports(body: ScheduleRequest) {
  return apiFetch<ReportBatch>("/api/v1/reports/orders/all-orders-by-order-date/schedule", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export type ReportFilters = {
  marketplaceId?: string;
  reportTypes?: string[]; // any of these; empty = all
  statuses?: ReportSyncStatus[]; // any of these; empty = all
};

// Latest report requests (newest first, at most `limit`), optionally filtered.
export function listReports(region: RegionCode, filters: ReportFilters = {}, limit = 100) {
  const query = new URLSearchParams({ region, limit: String(limit) });
  if (filters.marketplaceId) query.set("marketplaceId", filters.marketplaceId);
  for (const t of filters.reportTypes ?? []) query.append("reportType", t);
  for (const s of filters.statuses ?? []) query.append("status", s);
  return apiFetch<AmazonReport[]>(`/api/v1/reports?${query}`);
}

// ---------- Job queues: one for reports, one for Data Kiosk queries ----------

// What the queue panel needs from a queue. Jobs come back in the report shape (AmazonReport).
export type JobQueueApi = {
  noun: string; // "report" | "query"
  getQueue: () => Promise<ReportQueue>;
  cancel: (id: number) => Promise<unknown>;
  list: (region: RegionCode, filters: ReportFilters, limit: number) => Promise<AmazonReport[]>;
};

export const REPORT_QUEUE_API: JobQueueApi = {
  noun: "report",
  getQueue: getReportQueue,
  cancel: cancelReport,
  list: listReports,
};

export type OrderItemsSummary = {
  region: RegionCode;
  marketplaceId: string;
  rowCount: number;
  orderCount: number;
  firstPurchaseDate: string | null;
  lastPurchaseDate: string | null;
  lastStoredAt: string | null;
};

export function getOrderItemsSummary() {
  return apiFetch<OrderItemsSummary[]>("/api/v1/reports/orders/items/summary");
}

export type DatePeriod = { startDate: string; endDate: string }; // inclusive days

// Days of a marketplace covered by requests, per sync status (as in the request history).
export type ReportCoverage = {
  queued: DatePeriod[];
  processing: DatePeriod[];
  synced: DatePeriod[]; // already fetched
  failed: DatePeriod[];
  cancelled: DatePeriod[];
};

// Days of a marketplace covered by order report requests, per status, as merged periods.
export function getOrderReportCoverage(marketplaceId: string) {
  return apiFetch<ReportCoverage>(
    `/api/v1/reports/orders/all-orders-by-order-date/coverage?marketplaceId=${encodeURIComponent(marketplaceId)}`,
  );
}

// ---------- Listing reports (/api/v1/reports/listings/...) ----------

// Queues a listings snapshot (GET_MERCHANT_LISTINGS_ALL_DATA) per marketplace.
export function requestListingReports(marketplaceIds: string[]) {
  return apiFetch<ReportBatch>("/api/v1/reports/listings/all-listings", {
    method: "POST",
    body: JSON.stringify({ marketplaceIds }),
  });
}

export type ListingsSummary = {
  region: RegionCode;
  marketplaceId: string;
  listingCount: number;
  activeCount: number;
  totalQuantity: number;
  lastUpdatedAt: string | null;
};

export function getListingsSummary() {
  return apiFetch<ListingsSummary[]>("/api/v1/reports/listings/summary");
}

// ---------- Data Kiosk: SKU Economics (/api/v1/data-kiosk/economics/...) ----------

// Queues the SKU Economics query for the period as consecutive queries of `partitionDays` days.
export async function scheduleSkuEconomics(body: ScheduleRequest): Promise<ReportBatch> {
  const batch = await apiFetch<Omit<ReportBatch, "queued"> & { queued: DataKioskQuery[] }>(
    "/api/v1/data-kiosk/economics/sku-economics/schedule",
    { method: "POST", body: JSON.stringify(body) },
  );
  return { ...batch, queued: batch.queued.map(asJob) };
}

export function getSkuEconomicsCoverage(marketplaceId: string) {
  return apiFetch<ReportCoverage>(
    `/api/v1/data-kiosk/economics/sku-economics/coverage?marketplaceId=${encodeURIComponent(marketplaceId)}`,
  );
}

export type SkuEconomicsSummary = {
  region: RegionCode;
  marketplaceId: string;
  rowCount: number;
  skuCount: number;
  firstDate: string | null;
  lastDate: string | null;
  currencyCode: string | null;
  netUnitsSold: number;
  netProductSales: string; // decimal
  netProceedsTotal: string; // decimal
  lastUpdatedAt: string | null;
};

export function getSkuEconomicsSummary() {
  return apiFetch<SkuEconomicsSummary[]>("/api/v1/data-kiosk/economics/sku-economics/summary");
}

// ---------- Data Kiosk queue (/api/v1/data-kiosk/queries/...) ----------
// Its own table and worker: Data Kiosk queries don't wait behind reports.

export type DataKioskQuery = Omit<AmazonReport, "reportId" | "reportType"> & {
  queryId: string | null; // Amazon queryId, once submitted
  queryType: string;
  dataDocumentId: string | null;
};

type DataKioskQueue = { current: DataKioskQuery | null; pending: DataKioskQuery[]; counts: ReportQueue["counts"] };

// The queue panel renders jobs in the report shape.
const asJob = ({ queryId, queryType, ...q }: DataKioskQuery): AmazonReport => ({ ...q, reportId: queryId, reportType: queryType });

export async function getDataKioskQueue(): Promise<ReportQueue> {
  const q = await apiFetch<DataKioskQueue>("/api/v1/data-kiosk/queries/queue");
  return { current: q.current && asJob(q.current), pending: q.pending.map(asJob), counts: q.counts };
}

export function cancelDataKioskQuery(id: number) {
  return apiFetch<DataKioskQuery>(`/api/v1/data-kiosk/queries/${id}/cancel`, { method: "POST" });
}

// Latest Data Kiosk queries (newest first, at most `limit`); reportTypes filters by query type.
export async function listDataKioskQueries(region: RegionCode, filters: ReportFilters = {}, limit = 100) {
  const query = new URLSearchParams({ region, limit: String(limit) });
  if (filters.marketplaceId) query.set("marketplaceId", filters.marketplaceId);
  for (const t of filters.reportTypes ?? []) query.append("queryType", t);
  for (const s of filters.statuses ?? []) query.append("status", s);
  return (await apiFetch<DataKioskQuery[]>(`/api/v1/data-kiosk/queries?${query}`)).map(asJob);
}

export const DATA_KIOSK_QUEUE_API: JobQueueApi = {
  noun: "query",
  getQueue: getDataKioskQueue,
  cancel: cancelDataKioskQuery,
  list: listDataKioskQueries,
};
