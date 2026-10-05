"use client";

import { MarketplaceParticipations } from "../components/MarketplaceParticipations";
import { useRegion } from "../region";

export default function SellersPage() {
  const { region } = useRegion();
  return <MarketplaceParticipations key={region.code} region={region} />;
}
