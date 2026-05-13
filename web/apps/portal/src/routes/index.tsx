import { setAuthToken } from "@di-mata/api-client";
import { setToken } from "@di-mata/shared";
import { Input } from "@di-mata/ui";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  return (
    <main className="min-h-screen bg-[--color-background] flex flex-col">
      <header className="px-6 pt-10 pb-6 text-center">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[--color-primary] mb-4">
          <span className="text-[--color-primary-fg] font-bold text-lg">D</span>
        </div>
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Di Mata</h1>
        <p className="text-sm text-[--color-text-muted] mt-1">
          Plataforma de rastreabilidade da cadeia produtiva
        </p>
      </header>

      <div className="flex-1 px-4 pb-10 flex flex-col gap-4 max-w-md mx-auto w-full">
        <TrackCard />
        <Divider />
        <LoginCard />
      </div>
    </main>
  );
}

// ── Rastrear produto ──────────────────────────────────────────────────────────

function TrackCard() {
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [error, setError] = useState("");

  function handleTrack(e: React.FormEvent) {
    e.preventDefault();
    const hash = code.trim();
    if (!hash) {
      setError("Digite um código para rastrear.");
      return;
    }
    void navigate({ to: "/p/$hash", params: { hash } });
  }

  return (
    <div className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-6 space-y-4">
      <div>
        <h2 className="text-base font-semibold text-[--color-text-primary]">Rastrear produto</h2>
        <p className="text-sm text-[--color-text-muted] mt-0.5">
          Digite o código do QR code ou da etiqueta do produto.
        </p>
      </div>

      <form onSubmit={handleTrack} className="space-y-3">
        <Input
          inputSize="md"
          state={error ? "error" : "default"}
          value={code}
          onChange={(e) => {
            setCode(e.target.value);
            setError("");
          }}
          placeholder="Ex: abc123xyz"
          autoCapitalize="none"
          spellCheck={false}
        />
        {error && <p className="text-xs text-[--color-error]">{error}</p>}
        <button
          type="submit"
          className="w-full rounded-lg bg-[--color-primary] px-4 py-3 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity"
        >
          Buscar rastreabilidade
        </button>
      </form>
    </div>
  );
}

// ── Separador ─────────────────────────────────────────────────────────────────

function Divider() {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-[--color-border]" />
      <span className="text-xs text-[--color-text-muted]">ou acesse sua área</span>
      <div className="flex-1 h-px bg-[--color-border]" />
    </div>
  );
}

// ── Login ─────────────────────────────────────────────────────────────────────

function LoginCard() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [senha, setSenha] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !senha) {
      setError("Preencha e-mail e senha.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), senha }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Credenciais inválidas");
      }
      const { access_token } = await res.json();
      setToken(access_token);
      setAuthToken(access_token);
      void navigate({ to: "/minha-area" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao entrar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-6 space-y-4">
      <div>
        <h2 className="text-base font-semibold text-[--color-text-primary]">Minha área</h2>
        <p className="text-sm text-[--color-text-muted] mt-0.5">
          Acesse seu resumo de produção, lotes e QR codes.
        </p>
      </div>

      <form onSubmit={handleLogin} className="space-y-3">
        <Input
          type="email"
          inputSize="md"
          value={email}
          onChange={(e) => { setEmail(e.target.value); setError(""); }}
          placeholder="E-mail"
          autoComplete="email"
        />
        <Input
          type="password"
          inputSize="md"
          value={senha}
          onChange={(e) => { setSenha(e.target.value); setError(""); }}
          placeholder="Senha"
          autoComplete="current-password"
        />
        {error && <p className="text-xs text-[--color-error]">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[--color-primary] px-4 py-3 text-sm font-medium text-[--color-primary-fg] hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
