const TOKEN_KEY = "oficinas_token";
const PERFIL_KEY = "oficinas_perfil";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getPerfil(): string | null {
  return sessionStorage.getItem(PERFIL_KEY);
}

export function saveSession(token: string, perfil: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(PERFIL_KEY, perfil);
}

export function clearSession(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(PERFIL_KEY);
}
