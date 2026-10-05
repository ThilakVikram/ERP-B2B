"use client";

// Frame of the queued-job sections (Reports, Data Kiosk): the tab's content, then the queue status.
// The tabs themselves are routes in the sidebar (Section.tabs in ../../config).

import Link from "next/link";
import { StatusBanner } from "../shared";
import { ReportsProvider, useReports } from "./context";
import { QueueStatus } from "./QueueStatus";
import { CARD, EmptyState, LoadingRows } from "./shared";
import type { JobQueueApi } from "../../api";
import type { Region } from "../../config";

/** A section of queued Amazon jobs (Reports, Data Kiosk, ...): the tab's content, then the status of
 * its queue (`queueApi`) with history limited to `reportTypes` (unless `history` is false, when the
 * section shows it elsewhere). */
export function ReportsShell({
  region,
  queueApi,
  reportTypes,
  history = true,
  children,
}: {
  region: Region;
  queueApi: JobQueueApi; // the queue this section's jobs run in
  reportTypes: string[]; // job types this section queues (history filter)
  history?: boolean; // show the request history under the queue
  children: React.ReactNode;
}) {
  return (
    <ReportsProvider key={region.code} region={region}>
      <ReportsBody queueApi={queueApi} reportTypes={reportTypes} history={history}>
        {children}
      </ReportsBody>
    </ReportsProvider>
  );
}

function ReportsBody({
  queueApi,
  reportTypes,
  history,
  children,
}: {
  queueApi: JobQueueApi;
  reportTypes: string[];
  history: boolean;
  children: React.ReactNode;
}) {
  const { region, participations, loadError, marketplaces } = useReports();

  if (!participations) {
    return loadError ? (
      <StatusBanner status={{ kind: "error", text: loadError }} />
    ) : (
      <div className={CARD}>
        <LoadingRows count={3} />
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {marketplaces.length === 0 ? (
        <div className={CARD}>
          <EmptyState
            title={`No participating marketplaces stored for ${region.name}`}
            hint={
              <>
                Reports use the marketplaces from your seller account.{" "}
                <Link href="/integration/amazon/sellers" className="font-medium text-indigo-600 hover:underline dark:text-indigo-400">
                  Sync marketplace participations
                </Link>{" "}
                for {region.code} first.
              </>
            }
          />
        </div>
      ) : (
        children
      )}
      <QueueStatus api={queueApi} reportTypes={reportTypes} history={history} />
    </div>
  );
}
