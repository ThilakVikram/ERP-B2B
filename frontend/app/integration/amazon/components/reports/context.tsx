"use client";

// State shared by the report routes (/reports/orders, /reports/listings) and the queue status
// below them: the region's report marketplaces, the selected marketplace, and a version that is
// bumped whenever the queue moves so every section refetches.

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { listReportMarketplaces, type MarketplaceParticipation } from "../../api";
import type { Marketplace, Region } from "../../config";
import { errorText } from "../shared";

type ReportsState = {
  region: Region;
  participations: Record<string, MarketplaceParticipation> | null; // all regions, by marketplace ID
  loadError: string | null;
  marketplaces: Marketplace[]; // the region's report marketplaces
  selectedId: string; // "" while none
  select: (marketplaceId: string) => void;
  label: (marketplaceId: string) => string;
  version: number;
  refresh: () => void;
  justQueued: number[];
  markQueued: (ids: number[]) => void;
};

const ReportsContext = createContext<ReportsState | null>(null);

/** Key it by region so switching region starts fresh. */
export function ReportsProvider({ region, children }: { region: Region; children: React.ReactNode }) {
  const [participations, setParticipations] = useState<Record<string, MarketplaceParticipation> | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [marketplaceId, setMarketplaceId] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [justQueued, setJustQueued] = useState<number[]>([]);
  const refresh = useCallback(() => setVersion((v) => v + 1), []);

  useEffect(() => {
    let cancelled = false;
    listReportMarketplaces()
      .then((rows) => !cancelled && setParticipations(Object.fromEntries(rows.map((p) => [p.marketplaceId, p]))))
      .catch((err) => !cancelled && setLoadError(errorText(err)));
    return () => {
      cancelled = true;
    };
  }, []);

  const marketplaces: Marketplace[] = useMemo(
    () =>
      Object.values(participations ?? {})
        .filter((p) => p.region === region.code)
        .map((p) => ({ id: p.marketplaceId, code: p.countryCode, name: p.name })),
    [participations, region.code],
  );

  const label = useCallback(
    (id: string) => {
      const p = participations?.[id];
      return p ? `${p.countryCode} · ${p.name}` : id;
    },
    [participations],
  );

  const markQueued = useCallback(
    (ids: number[]) => {
      setJustQueued(ids);
      refresh();
    },
    [refresh],
  );

  const selectedId = marketplaces.find((m) => m.id === marketplaceId)?.id ?? marketplaces[0]?.id ?? "";

  return (
    <ReportsContext
      value={{
        region,
        participations,
        loadError,
        marketplaces,
        selectedId,
        select: setMarketplaceId,
        label,
        version,
        refresh,
        justQueued,
        markQueued,
      }}
    >
      {children}
    </ReportsContext>
  );
}

export function useReports(): ReportsState {
  const state = useContext(ReportsContext);
  if (!state) throw new Error("useReports must be used inside ReportsProvider");
  return state;
}
