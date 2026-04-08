export const TOKEN_KEY = "tdl_api_token";

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(t: string): void {
  localStorage.setItem(TOKEN_KEY, t);
}

export const apiBase = import.meta.env.VITE_API_BASE || "";

export function apiUrl(path: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `${apiBase}${p}`;
}

export function authHeaders(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const t = getToken();
  if (t) {
    h["Authorization"] = `Bearer ${t}`;
  }
  return h;
}

export function mediaUrl(relPath: string): string {
  const q = new URLSearchParams({ path: relPath });
  const t = getToken();
  if (t) {
    q.set("token", t);
  }
  return apiUrl(`/api/files/media?${q.toString()}`);
}
