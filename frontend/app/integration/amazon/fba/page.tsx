"use client";

import { FbaInventory } from "../components/FbaInventory";
import { useRegion } from "../region";

export default function FbaPage() {
  const { region } = useRegion();
  return <FbaInventory key={region.code} region={region} />;
}
