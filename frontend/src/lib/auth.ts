import type { User, LoginResponse } from "./types";

const TOKEN_KEY = "lims_token";
const USER_KEY = "lims_user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export function getCurrentUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setCurrentUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function logout(): void {
  removeToken();
  if (typeof window !== "undefined") {
    window.location.href = "/login";
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ??
    (typeof window !== "undefined"
      ? `${window.location.protocol}//${window.location.hostname}:8088`
      : "http://localhost:8088");
  const res = await fetch(`${apiUrl}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(err.detail || "Login failed");
  }

  const data: LoginResponse = await res.json();
  setToken(data.access_token);
  setCurrentUser(data.user);
  return data;
}
