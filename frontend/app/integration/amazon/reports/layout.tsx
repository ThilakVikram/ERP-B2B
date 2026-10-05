"use client";

import { REPORT_QUEUE_API } from "../api";
import { ReportsShell } from "../components/reports/ReportsShell";
import { REPORT_TYPES } from "../config";
import { useRegion } from "../region";

// Tabs are Section.tabs in ../config (shown in the sidebar). The request history is on the section's
// own page (./page.tsx), not under each tab.
export default function ReportsLayout({ children }: LayoutProps<"/integration/amazon/reports">) {
  const { region } = useRegion();
  return (
    <ReportsShell region={region} queueApi={REPORT_QUEUE_API} reportTypes={REPORT_TYPES} history={false}>
      {children}
    </ReportsShell>
  );
}
