const TOKEN_KEY = "access_token";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

/** Chama `cb` com o token salvo caso ele exista — use em main.tsx para restaurar auth. */
export function restoreToken(cb: (token: string) => void): void {
  const token = getToken();
  if (token) cb(token);
}
