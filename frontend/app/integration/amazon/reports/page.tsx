"use client";

import { REPORT_QUEUE_API } from "../api";
import { ReportHistory } from "../components/reports/QueueStatus";
import { REPORT_TYPES } from "../config";

export default function ReportsPage() {
  return (
    <ReportHistory
      api={REPORT_QUEUE_API}
      reportTypes={REPORT_TYPES}
      emptyHint="Queue some from the Orders or Listings tab."
    />
  );
}
