import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/app/veiculos/$placa")({
  component: VeiculoDetalhe,
});

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface Veiculo {
  id: string;
  placa: string;
  marca: string | null;
  modelo: string | null;
  ano_fab: number | null;
  ano_mod: number | null;
  cor: string | null;
  tipo: string | null;
  historico_publico: HistoricoPublico[];
}

interface HistoricoPublico {
  id: string;
  data_servico: string;
  km_entrada: number | null;
  resumo_publico: string;
}

interface ItemOSHistorico {
  tipo: string;
  descricao: string;
  quantidade: number;
  preco_unitario: number;
  subtotal: number;
}

interface HistoricoEntrada {
  os_id: string;
  numero_os: string;
  data_servico: string;
  km_entrada: number | null;
  descricao_problema: string;
  total_pecas: number;
  total_servicos: number;
  total_final: number;
  compartilhar_historico: boolean;
  itens: ItemOSHistorico[];
}

const BRL = (v: number) =>
  v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const DATA = (s: string) =>
  new Date(s + "T00:00:00").toLocaleDateString("pt-BR");

// ─── Componentes ──────────────────────────────────────────────────────────────

function VeiculoCard({ veiculo }: { veiculo: Veiculo }) {
  const anoLabel = veiculo.ano_fab
    ? veiculo.ano_mod && veiculo.ano_mod !== veiculo.ano_fab
      ? `${veiculo.ano_fab}/${veiculo.ano_mod}`
      : String(veiculo.ano_fab)
    : null;

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start gap-6">
          <div className="shrink-0 rounded-lg border-2 border-[--color-primary] bg-[--color-primary]/10 px-5 py-3 text-center">
            <p className="font-mono font-bold text-2xl tracking-widest text-[--color-primary]">
              {veiculo.placa}
            </p>
            {veiculo.tipo && (
              <p className="text-xs uppercase tracking-wide text-[--color-text-muted] mt-1">
                {veiculo.tipo}
              </p>
            )}
          </div>
          <dl className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-3 text-sm flex-1">
            <div>
              <dt className="text-xs text-[--color-text-muted] mb-0.5">Marca</dt>
              <dd className="font-medium text-[--color-text-primary]">{veiculo.marca ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[--color-text-muted] mb-0.5">Modelo</dt>
              <dd className="font-medium text-[--color-text-primary]">{veiculo.modelo ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[--color-text-muted] mb-0.5">Ano</dt>
              <dd className="font-medium text-[--color-text-primary]">{anoLabel ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-xs text-[--color-text-muted] mb-0.5">Cor</dt>
              <dd className="font-medium text-[--color-text-primary]">{veiculo.cor ?? "—"}</dd>
            </div>
          </dl>
        </div>
      </CardContent>
    </Card>
  );
}

function EntradaTimeline({ entrada }: { entrada: HistoricoEntrada }) {
  const pecas    = entrada.itens.filter((i) => i.tipo === "PECA");
  const servicos = entrada.itens.filter((i) => i.tipo === "SERVICO");
  const [expandido, setExpandido] = useState(false);

  return (
    <div className="relative pl-8">
      {/* linha vertical + ponto */}
      <div className="absolute left-0 top-2 h-full w-px bg-[--color-border]" />
      <div className="absolute left-[-5px] top-2 h-3 w-3 rounded-full border-2 border-[--color-primary] bg-[--color-surface]" />

      <div className="rounded-lg border border-[--color-border] bg-[--color-surface] p-4 mb-6">
        {/* Cabeçalho */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-[--color-text-primary]">
                {DATA(entrada.data_servico)}
              </span>
              {entrada.km_entrada && (
                <span className="text-xs text-[--color-text-muted] bg-[--color-background] rounded px-1.5 py-0.5">
                  {entrada.km_entrada.toLocaleString("pt-BR")} km
                </span>
              )}
              {entrada.compartilhar_historico && (
                <Badge variant="secondary" className="text-[10px]">Público</Badge>
              )}
            </div>
            <p className="text-xs text-[--color-text-muted] mt-0.5 font-mono">{entrada.numero_os}</p>
          </div>
          <div className="text-right shrink-0">
            <p className="text-sm font-semibold text-[--color-text-primary]">
              {BRL(entrada.total_final)}
            </p>
            <Link
              to="/app/os/$osId"
              params={{ osId: entrada.os_id }}
              className="text-xs text-[--color-primary] hover:underline"
            >
              Ver OS →
            </Link>
          </div>
        </div>

        {/* Problema */}
        <p className="text-sm text-[--color-text-secondary] mb-3">{entrada.descricao_problema}</p>

        {/* Totalizadores */}
        {(entrada.total_pecas > 0 || entrada.total_servicos > 0) && (
          <div className="flex flex-wrap gap-4 text-xs text-[--color-text-muted] mb-3">
            {entrada.total_servicos > 0 && (
              <span>Serviços: <strong className="text-[--color-text-primary]">{BRL(entrada.total_servicos)}</strong></span>
            )}
            {entrada.total_pecas > 0 && (
              <span>Peças: <strong className="text-[--color-text-primary]">{BRL(entrada.total_pecas)}</strong></span>
            )}
          </div>
        )}

        {/* Itens expandíveis */}
        {entrada.itens.length > 0 && (
          <>
            <button
              type="button"
              onClick={() => setExpandido((v) => !v)}
              className="text-xs text-[--color-primary] hover:underline"
            >
              {expandido ? "▲ Ocultar itens" : `▼ Ver itens (${entrada.itens.length})`}
            </button>

            {expandido && (
              <div className="mt-3 space-y-2">
                {servicos.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-1">
                      Serviços
                    </p>
                    <ul className="space-y-1">
                      {servicos.map((item, i) => (
                        <li key={i} className="flex justify-between text-sm">
                          <span className="text-[--color-text-secondary]">
                            {item.descricao}
                            <span className="text-[--color-text-muted] ml-1">×{item.quantidade}</span>
                          </span>
                          <span className="text-[--color-text-primary] font-mono">{BRL(item.subtotal)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {pecas.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-1">
                      Peças
                    </p>
                    <ul className="space-y-1">
                      {pecas.map((item, i) => (
                        <li key={i} className="flex justify-between text-sm">
                          <span className="text-[--color-text-secondary]">
                            {item.descricao}
                            <span className="text-[--color-text-muted] ml-1">×{item.quantidade} @ {BRL(item.preco_unitario)}</span>
                          </span>
                          <span className="text-[--color-text-primary] font-mono">{BRL(item.subtotal)}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── Page ──────────────────────────────────────────────────────────────────────

function VeiculoDetalhe() {
  const { placa } = Route.useParams();
  const navigate = useNavigate();

  const { data: veiculo, isLoading: loadingVeiculo, isError } = useQuery({
    queryKey: ["veiculo", placa],
    queryFn: () => api.get<Veiculo>(`/veiculos/${encodeURIComponent(placa)}`),
    retry: false,
  });

  const { data: historico, isLoading: loadingHistorico } = useQuery({
    queryKey: ["veiculo-historico", placa],
    queryFn: () => api.get<HistoricoEntrada[]>(`/veiculos/${encodeURIComponent(placa)}/historico`),
    enabled: !!veiculo,
  });

  const totalServicado = historico?.reduce((s, e) => s + e.total_final, 0) ?? 0;

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center justify-between">
        <Link to="/app/veiculos" className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary]">
          ← Veículos
        </Link>
        {veiculo && (
          <Button
            size="sm"
            onClick={() =>
              void navigate({
                to: "/app/os/nova",
                search: { placa: veiculo.placa },
              })
            }
          >
            + Nova OS
          </Button>
        )}
      </div>

      {/* Card do veículo */}
      {loadingVeiculo ? (
        <Card><CardContent className="pt-6"><Skeleton className="h-24 w-full" /></CardContent></Card>
      ) : isError ? (
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-[--color-error]">Veículo "{placa}" não encontrado.</p>
          </CardContent>
        </Card>
      ) : veiculo ? (
        <VeiculoCard veiculo={veiculo} />
      ) : null}

      {/* Histórico desta oficina */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>
              Histórico de OS
              {historico && historico.length > 0 && (
                <span className="ml-2 text-sm font-normal text-[--color-text-muted]">
                  ({historico.length} OS · {BRL(totalServicado)} total)
                </span>
              )}
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loadingHistorico ? (
            <div className="space-y-4">
              {[1, 2].map((i) => <Skeleton key={i} className="h-28 w-full" />)}
            </div>
          ) : !historico || historico.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-6 text-center">
              Nenhuma OS fechada para este veículo.
            </p>
          ) : (
            <div className="mt-4">
              {historico.map((entrada) => (
                <EntradaTimeline key={entrada.os_id} entrada={entrada} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Histórico público de outras oficinas */}
      {veiculo && veiculo.historico_publico.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Histórico público
              <span className="ml-2 text-sm font-normal text-[--color-text-muted]">
                (outras oficinas que compartilharam)
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {veiculo.historico_publico.map((h) => (
                <div
                  key={h.id}
                  className="rounded-md border border-[--color-border] bg-[--color-background] p-3 text-sm"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-[--color-text-primary]">{DATA(h.data_servico)}</span>
                    {h.km_entrada && (
                      <span className="text-xs text-[--color-text-muted]">
                        {h.km_entrada.toLocaleString("pt-BR")} km
                      </span>
                    )}
                  </div>
                  <p className="text-[--color-text-secondary]">{h.resumo_publico}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// useState precisa ser importado
import { useState } from "react";
