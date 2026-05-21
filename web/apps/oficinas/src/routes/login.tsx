import { ApiError, api } from "@/lib/api";
import { saveSession } from "@/lib/auth";
import { useTenant } from "@di-mata/theme";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/login")({
  component: LoginPage,
});

interface TokenResponse {
  access_token: string;
  token_type: string;
  perfil: string;
}

function LoginPage() {
  const navigate = useNavigate();
  const tenant = useTenant();
  const [identificador, setIdentificador] = useState("");
  const [senha, setSenha] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const data = await api.post<TokenResponse>("/auth/login", { identificador, senha });
      saveSession(data.access_token, data.perfil);
      void navigate({ to: "/app" });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError("Identificador ou senha inválidos.");
      } else if (err instanceof ApiError && err.status === 403) {
        setError("Usuário inativo. Contate o administrador.");
      } else {
        setError("Erro de conexão. Tente novamente.");
      }
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
              <label
                htmlFor="identificador"
                className="text-sm font-medium text-[--color-text-primary]"
              >
                E-mail ou WhatsApp
              </label>
              <input
                id="identificador"
                type="text"
                required
                value={identificador}
                onChange={(e) => setIdentificador(e.target.value)}
                placeholder="email@exemplo.com ou +5511999990000"
                className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="senha" className="text-sm font-medium text-[--color-text-primary]">
                Senha
              </label>
              <input
                id="senha"
                type="password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
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
