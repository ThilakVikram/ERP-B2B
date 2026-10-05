// Session handling for the backend's JWT auth (/api/v1/auth/...).

import { apiFetch } from "./api";

export type User = {
  id: number;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  isActive: boolean;
  createdAt: string;
};

type TokenResponse = {
  accessToken: string;
  tokenType: string;
  expiresIn: number; // seconds
  user: User;
};

export type SignupData = {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
};

const TOKEN_KEY = "accessToken";
const EXPIRES_KEY = "accessTokenExpiresAt";
const USER_KEY = "user";

export function getToken(): string | null {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    const expiresAt = Number(localStorage.getItem(EXPIRES_KEY));
    if (!token || (expiresAt && Date.now() >= expiresAt)) return null;
    return token;
  } catch {
    return null;
  }
}

export function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function saveSession({ accessToken, expiresIn, user }: TokenResponse) {
  try {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(EXPIRES_KEY, String(Date.now() + expiresIn * 1000));
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {
    // Storage unavailable (private mode); the session just won't persist.
  }
}

export function clearSession() {
  try {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EXPIRES_KEY);
    localStorage.removeItem(USER_KEY);
  } catch {}
}

export async function login(email: string, password: string, rememberMe: boolean) {
  const res = await apiFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password, rememberMe }),
    auth: false,
  });
  saveSession(res);
  return res.user;
}

export async function signup(data: SignupData) {
  const res = await apiFetch<TokenResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify(data),
    auth: false,
  });
  saveSession(res);
  return res.user;
}

export async function fetchMe() {
  const user = await apiFetch<User>("/api/v1/auth/me");
  try {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch {}
  return user;
}

/** Where to go after login: the ?next= path if it is a local path, else the default. */
export function redirectTarget(fallback = "/home") {
  const next = new URLSearchParams(window.location.search).get("next");
  return next && next.startsWith("/") && !next.startsWith("//") ? next : fallback;
}
