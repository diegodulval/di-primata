import createClient from "openapi-fetch";
import type { paths } from "./generated/schema";

const BASE_URL =
  (typeof import.meta !== "undefined" && (import.meta as { env?: { VITE_API_URL?: string } }).env?.VITE_API_URL) ||
  "http://localhost:8000";

let _authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  _authToken = token;
}

export const api = createClient<paths>({
  baseUrl: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.use({
  onRequest({ request }) {
    if (_authToken) {
      request.headers.set("Authorization", `Bearer ${_authToken}`);
    }
    return request;
  },
  onResponse({ response }) {
    if (response.status === 401) {
      _authToken = null;
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    }
    return response;
  },
});
