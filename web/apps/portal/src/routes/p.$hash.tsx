import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Skeleton } from "@di-mata/ui";
import { api } from "@di-mata/api-client";

// Tipo temporário até geração do schema OpenAPI
interface LotePublico {
  lote_id: string;
  qr_hash: string;
  produto: string;
  safra?: string;
  unidade_nome?: string;
  certificacoes?: string[];
  gerado_em: string;
}

export const Route = createFileRoute("/p/$hash")({
  component: PortalPage,
});

function PortalPage() {
  const { hash } = Route.useParams();
  const [lote, setLote] = useState<LotePublico | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchLote() {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const { data, error: apiError } = await (api.GET as any)("/p/{qr_hash}", {
          params: { path: { qr_hash: hash } },
        });
        if (apiError) throw new Error("Lote não encontrado");
        setLote(data as LotePublico);
      } catch {
        setError("Não foi possível carregar as informações deste produto.");
      } finally {
        setLoading(false);
      }
    }
    void fetchLote();
  }, [hash]);

  if (loading) return <PortalSkeleton />;

  if (error || !lote) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6">
        <div className="text-center">
          <p className="text-[--color-error] font-medium">{error}</p>
          <p className="text-[--color-text-muted] text-sm mt-2">Código: {hash}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-6 max-w-lg mx-auto">
      <header className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">{lote.produto}</h1>
        {lote.safra && (
          <p className="text-[--color-text-secondary] text-sm mt-1">Safra {lote.safra}</p>
        )}
      </header>
      <section className="space-y-4">
        {lote.unidade_nome && (
          <InfoRow label="Unidade Produtiva" value={lote.unidade_nome} />
        )}
        <InfoRow label="Lote" value={lote.lote_id} mono />
        <InfoRow label="Emitido em" value={new Date(lote.gerado_em).toLocaleDateString("pt-BR")} />
        {lote.certificacoes && lote.certificacoes.length > 0 && (
          <div>
            <dt className="text-xs font-medium text-[--color-text-muted] uppercase tracking-wide">
              Certificações
            </dt>
            <dd className="mt-1 flex flex-wrap gap-2">
              {lote.certificacoes.map((cert) => (
                <span
                  key={cert}
                  className="rounded-full bg-[--color-primary-50] px-3 py-0.5 text-xs font-medium text-[--color-primary-900]"
                >
                  {cert}
                </span>
              ))}
            </dd>
          </div>
        )}
      </section>
    </main>
  );
}

function InfoRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <dl>
      <dt className="text-xs font-medium text-[--color-text-muted] uppercase tracking-wide">
        {label}
      </dt>
      <dd className={`mt-0.5 text-[--color-text-primary] ${mono ? "font-mono text-sm" : ""}`}>
        {value}
      </dd>
    </dl>
  );
}

function PortalSkeleton() {
  return (
    <main className="min-h-screen p-6 max-w-lg mx-auto">
      <div className="mb-8 text-center space-y-2">
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-4 w-24 mx-auto" />
      </div>
      <div className="space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="space-y-1">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-5 w-48" />
          </div>
        ))}
      </div>
    </main>
  );
}
