"use client";

// The selected region, shared by every Amazon section route and kept across reloads.

import { createContext, useContext, useSyncExternalStore } from "react";
import { REGIONS, type Region, type RegionCode } from "./config";

const STORAGE_KEY = "itrend.amazon.region";
const DEFAULT_REGION = REGIONS[0].code;

// localStorage can be unavailable (private mode, blocked storage); fall back to memory.
let memory: RegionCode = DEFAULT_REGION;
const listeners = new Set<() => void>();

const isRegionCode = (v: string | null): v is RegionCode => REGIONS.some((r) => r.code === v);

function read(): RegionCode {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (isRegionCode(saved)) return saved;
  } catch {}
  return memory;
}

function write(code: RegionCode) {
  memory = code;
  try {
    localStorage.setItem(STORAGE_KEY, code);
  } catch {}
  listeners.forEach((notify) => notify());
}

function subscribe(notify: () => void) {
  listeners.add(notify);
  window.addEventListener("storage", notify); // other tabs
  return () => {
    listeners.delete(notify);
    window.removeEventListener("storage", notify);
  };
}

type RegionState = { region: Region; setRegionCode: (code: RegionCode) => void };

const RegionContext = createContext<RegionState | null>(null);

export function RegionProvider({ children }: { children: React.ReactNode }) {
  const regionCode = useSyncExternalStore(subscribe, read, () => DEFAULT_REGION);
  const region = REGIONS.find((r) => r.code === regionCode) ?? REGIONS[0];
  return <RegionContext value={{ region, setRegionCode: write }}>{children}</RegionContext>;
}

export function useRegion(): RegionState {
  const state = useContext(RegionContext);
  if (!state) throw new Error("useRegion must be used inside RegionProvider");
  return state;
}
