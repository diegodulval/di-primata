import { formatDate } from "@di-mata/shared";
import { Skeleton } from "@di-mata/ui";
import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

const TIPO_LABEL: Record<string, string> = {
  ENTRADA_INSUMO: "Entrada de insumo",
  OPERACAO: "Operação",
  CTRL_QUALIDADE: "Controle de qualidade",
  ANOMALIA: "Anomalia",
  MOVIMENTACAO: "Movimentação",
  COLHEITA: "Colheita",
  EXPEDICAO: "Expedição",
};

const TIPO_UNIDADE_LABEL: Record<string, string> = {
  TALHAO: "Talhão",
  VIVEIRO: "Viveiro",
  BAIA: "Baia",
  LINHA_PRODUCAO: "Linha de Produção",
  TEAR: "Tear",
  ATELIE: "Ateliê",
  OUTRO: "Outro",
};

const brl = (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// ── Tipos ─────────────────────────────────────────────────────────────────────

type EventoPublico = {
  id: string;
  tipo_evento: string;
  descricao: string;
  custo: number | null;
  capturado_em: string;
  origem: string;
};

type SnapshotPublico = {
  codigo_lote: string;
  produto: string;
  iniciado_em: string;
  encerrado_em: string | null;
  unidade: { nome: string; tipo: string } | null;
  protocolo: { nome: string; versao: string } | null;
  total_custo: number;
  total_atividades: number;
  autodeclarado: boolean;
  autodeclarado_em: string | null;
  eventos: EventoPublico[];
};

// ── Rota ──────────────────────────────────────────────────────────────────────

export const Route = createFileRoute("/p/$hash")({
  component: ProdutoPage,
});

function ProdutoPage() {
  const { hash } = Route.useParams();
  const [snapshot, setSnapshot] = useState<SnapshotPublico | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/p/${hash}`)
      .then((res) => {
        if (!res.ok) throw new Error("not found");
        return res.json() as Promise<SnapshotPublico>;
      })
      .then(setSnapshot)
      .catch(() => setError("Produto não encontrado ou QR code inválido."))
      .finally(() => setLoading(false));
  }, [hash]);

  if (loading) return <ProdutoSkeleton />;

  if (error || !snapshot) {
    return (
      <main className="flex min-h-screen items-center justify-center p-6 bg-[--color-background]">
        <div className="text-center space-y-2">
          <p className="font-medium text-[--color-error]">{error}</p>
          <p className="text-xs text-[--color-text-muted] font-mono">{hash}</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[--color-background]">
      <header className="bg-[--color-surface] border-b border-[--color-border] px-5 py-4 flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-[--color-primary] flex items-center justify-center">
          <span className="text-[--color-primary-fg] font-bold text-xs">D</span>
        </div>
        <span className="text-sm font-medium text-[--color-text-muted]">
          Di Mata · Rastreabilidade
        </span>
      </header>

      <div className="max-w-lg mx-auto px-4 py-6 space-y-4">
        {/* Produto e unidade */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5">
          <h1 className="text-xl font-bold text-[--color-text-primary]">{snapshot.produto}</h1>
          {snapshot.unidade && (
            <p className="text-sm text-[--color-text-muted] mt-1">
              {snapshot.unidade.nome}
              <span className="mx-1.5">·</span>
              {TIPO_UNIDADE_LABEL[snapshot.unidade.tipo] ?? snapshot.unidade.tipo}
            </p>
          )}
          <p className="text-xs text-[--color-text-muted] font-mono mt-2">
            Lote: {snapshot.codigo_lote}
          </p>
          <p className="text-xs text-[--color-text-muted] mt-1">
            {formatDate(snapshot.iniciado_em)}
            {snapshot.encerrado_em && <> → {formatDate(snapshot.encerrado_em)}</>}
          </p>
        </section>

        {/* Badge de autodeclaração */}
        {snapshot.autodeclarado && (
          <section className="rounded-2xl border border-[--color-primary] bg-[--color-primary]/5 p-4 flex items-start gap-3">
            <div className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full bg-[--color-primary] flex items-center justify-center">
              <svg
                aria-hidden="true"
                viewBox="0 0 12 12"
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ color: "var(--color-primary-fg)" }}
              >
                <path d="M2 6l2.5 2.5L10 3.5" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-[--color-text-primary]">
                Verificado pelo engenheiro responsável
              </p>
              {snapshot.autodeclarado_em && (
                <p className="text-xs text-[--color-text-muted] mt-0.5">
                  Em {formatDate(snapshot.autodeclarado_em)}
                </p>
              )}
            </div>
          </section>
        )}

        {/* Resumo numérico */}
        <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] px-5 py-4 flex justify-around">
          <div className="text-center">
            <p className="text-2xl font-bold text-[--color-text-primary]">
              {snapshot.total_atividades}
            </p>
            <p className="text-xs text-[--color-text-muted] mt-0.5">atividades</p>
          </div>
          <div className="w-px bg-[--color-border]" />
          <div className="text-center">
            <p className="text-xl font-bold text-[--color-text-primary]">
              {brl(snapshot.total_custo)}
            </p>
            <p className="text-xs text-[--color-text-muted] mt-0.5">em insumos</p>
          </div>
        </section>

        {/* Protocolo (quando houver) */}
        {snapshot.protocolo && (
          <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-4">
            <p className="text-xs font-medium text-[--color-text-muted] uppercase tracking-wide mb-1">
              Protocolo
            </p>
            <p className="text-sm font-medium text-[--color-text-primary]">
              {snapshot.protocolo.nome}
            </p>
            <p className="text-xs text-[--color-text-muted]">v{snapshot.protocolo.versao}</p>
          </section>
        )}

        {/* Timeline de eventos */}
        {snapshot.eventos.length > 0 && (
          <section className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5">
            <h2 className="text-sm font-semibold text-[--color-text-primary] mb-4">
              Histórico de atividades
            </h2>
            <ol>
              {snapshot.eventos.map((ev, i) => (
                <li key={ev.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-2.5 h-2.5 rounded-full bg-[--color-primary] mt-1 flex-shrink-0" />
                    {i < snapshot.eventos.length - 1 && (
                      <div className="w-px flex-1 min-h-4 bg-[--color-border] my-1" />
                    )}
                  </div>
                  <div className="pb-4 min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-[--color-text-primary]">
                          {TIPO_LABEL[ev.tipo_evento] ?? ev.tipo_evento}
                        </p>
                        <p className="text-xs text-[--color-text-muted] mt-0.5">
                          {formatDate(ev.capturado_em)}
                        </p>
                      </div>
                      {ev.custo != null && (
                        <span className="text-sm font-semibold text-[--color-text-primary] whitespace-nowrap flex-shrink-0">
                          {brl(ev.custo)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-[--color-text-secondary] mt-1">{ev.descricao}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )}

        {/* Rodapé */}
        <footer className="py-4 text-center space-y-1">
          <p className="text-xs text-[--color-text-muted]">
            Informações verificadas por Di Mata Rastreabilidade
          </p>
          <p className="text-xs text-[--color-text-muted] font-mono">{snapshot.codigo_lote}</p>
        </footer>
      </div>
    </main>
  );
}

function ProdutoSkeleton() {
  return (
    <main className="min-h-screen bg-[--color-background]">
      <div className="bg-[--color-surface] border-b border-[--color-border] h-14" />
      <div className="max-w-lg mx-auto px-4 py-6 space-y-4">
        <div className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-2">
          <Skeleton className="h-6 w-44" />
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-3 w-36" />
        </div>
        <div className="rounded-2xl border border-[--color-border] bg-[--color-surface] p-5 space-y-4">
          <Skeleton className="h-5 w-40" />
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <Skeleton className="w-2.5 h-2.5 rounded-full mt-1 flex-shrink-0" />
              <div className="space-y-1.5 flex-1">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
                <Skeleton className="h-4 w-48" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
