import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { setAuthToken } from "@di-mata/api-client";
import { useTenant } from "@di-mata/theme";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

function LoginPage() {
  const navigate = useNavigate();
  const tenant = useTenant();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const isDev = import.meta.env.DEV;
      if (isDev) console.debug("[login] POST /api/auth/login", { email });

      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, senha: password }),
      });

      if (!res.ok) {
        if (isDev) {
          const body = await res.json().catch(() => null);
          console.warn("[login] falhou", { status: res.status, body });
        }
        setError("E-mail ou senha inválidos.");
        return;
      }

      const { access_token } = (await res.json()) as { access_token: string };
      if (isDev) console.debug("[login] ok, navegando para /dashboard");
      sessionStorage.setItem("access_token", access_token);
      setAuthToken(access_token);
      void navigate({ to: "/dashboard" });
    } catch (err) {
      if (import.meta.env.DEV) console.error("[login] erro de conexão", err);
      setError("Erro de conexão. Tente novamente.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[--color-background] p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle>{tenant.brandName}</CardTitle>
          <p className="text-sm text-[--color-text-muted] mt-1">Acesse sua conta</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={(e) => void handleSubmit(e)} className="space-y-4">
            <div className="space-y-1">
              <label htmlFor="email" className="text-sm font-medium text-[--color-text-primary]">
                E-mail
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="password" className="text-sm font-medium text-[--color-text-primary]">
                Senha
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            {error && <p className="text-sm text-[--color-error]">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
