// Shared fetch helper for the itrend backend.

import { clearSession, getToken } from "./auth";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

type ApiInit = RequestInit & {
  /** false for public endpoints (login/signup): no token is sent and a 401 is not treated as an expired session. */
  auth?: boolean;
};

function errorMessage(body: unknown, fallback: string): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  // FastAPI validation errors: [{ msg: "Value error, Passwords do not match", ... }]
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") {
    return detail[0].msg.replace(/^Value error, /, "");
  }
  return fallback;
}

export async function apiFetch<T>(path: string, { auth = true, ...init }: ApiInit = {}): Promise<T> {
  const token = auth ? getToken() : null;
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) {
    if (auth && res.status === 401) {
      // Token missing, expired or revoked: send the user back to login.
      clearSession();
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      // Outside React, so no router here; a full reload also drops stale client state.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign(`/login?next=${next}`);
    }
    const body = await res.json().catch(() => null);
    throw new ApiError(
      errorMessage(body, res.statusText || `Request failed (${res.status})`),
      res.status,
    );
  }
  return res.json() as Promise<T>;
}
