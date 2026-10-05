"use client";

import { DATA_KIOSK_QUEUE_API } from "../api";
import { ReportsShell } from "../components/reports/ReportsShell";
import { useRegion } from "../region";

// Tabs are Section.tabs in ../config (shown in the sidebar).
const QUERY_TYPES = ["DATA_KIOSK_SKU_ECONOMICS"];

export default function DataKioskLayout({ children }: LayoutProps<"/integration/amazon/data_kiosk">) {
  const { region } = useRegion();
  return (
    <ReportsShell region={region} queueApi={DATA_KIOSK_QUEUE_API} reportTypes={QUERY_TYPES}>
      {children}
    </ReportsShell>
  );
}
