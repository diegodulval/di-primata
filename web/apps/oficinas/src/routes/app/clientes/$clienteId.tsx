import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/clientes/$clienteId")({
  component: ClienteDetalhe,
});

interface Cliente {
  id: string;
  nome: string;
  tipo_pessoa: string | null;
  cpf_cnpj: string | null;
  rg: string | null;
  apelido: string | null;
  sexo: string | null;
  telefone: string | null;
  celular: string | null;
  email: string | null;
  cep: string | null;
  endereco: string | null;
  cidade: string | null;
  uf: string | null;
  inscricao_estadual: string | null;
  consumidor_final: boolean;
  indicador_ie: string;
  observacoes: string | null;
  ativo: boolean;
}

interface VeiculoResumo {
  placa: string;
  marca: string | null;
  modelo: string | null;
  ano_fab: number | null;
  ano_mod: number | null;
  cor: string | null;
  tipo: string | null;
}

interface ClienteVeiculo {
  id: string;
  veiculo_id: string;
  data_inicio: string;
  data_fim: string | null;
  ativo: boolean;
  veiculo: VeiculoResumo | null;
}

const INPUT_CLS =
  "w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]";

function VincularVeiculoForm({ clienteId, onClose }: { clienteId: string; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [placa, setPlaca] = useState("");
  const [error, setError] = useState<string | null>(null);

  const vincular = useMutation({
    mutationFn: async () => {
      const veiculo = await api.get<{ id: string }>(`/veiculos/${encodeURIComponent(placa.toUpperCase())}`);
      await api.post(`/clientes/${clienteId}/veiculos`, { veiculo_id: veiculo.id });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["cliente-veiculos", clienteId] });
      onClose();
    },
    onError: (err: Error) => setError(err.message),
  });

  return (
    <form
      onSubmit={(e: FormEvent) => { e.preventDefault(); vincular.mutate(); }}
      className="flex gap-2 items-end mt-4"
    >
      <div className="space-y-1 flex-1 max-w-xs">
        <label htmlFor="placa-vincular" className="text-sm font-medium text-[--color-text-primary]">
          Placa
        </label>
        <input
          id="placa-vincular"
          required
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC1234 ou ABC1D23"
          maxLength={8}
          className={`${INPUT_CLS} font-mono uppercase`}
        />
      </div>
      <Button type="submit" size="sm" disabled={vincular.isPending}>
        {vincular.isPending ? "Vinculando..." : "Vincular"}
      </Button>
      <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
      {error && <p className="text-sm text-[--color-error] self-center">{error}</p>}
    </form>
  );
}

function Campo({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div>
      <dt className="text-xs text-[--color-text-muted] mb-0.5">{label}</dt>
      <dd className="text-sm text-[--color-text-primary]">{value || "—"}</dd>
    </div>
  );
}

function VeiculoCard({ v, onDesassociar }: { v: ClienteVeiculo; onDesassociar: () => void }) {
  const vei = v.veiculo;
  const anoLabel = vei?.ano_fab
    ? vei.ano_mod && vei.ano_mod !== vei.ano_fab
      ? `${vei.ano_fab}/${vei.ano_mod}`
      : String(vei.ano_fab)
    : null;

  return (
    <div
      className={`rounded-lg border p-4 flex items-start justify-between gap-4 ${
        v.ativo
          ? "border-[--color-border] bg-[--color-surface]"
          : "border-[--color-border] bg-[--color-background] opacity-60"
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Placa */}
        {vei?.placa ? (
          <Link
            to="/app/veiculos/$placa"
            params={{ placa: vei.placa }}
            className="shrink-0 rounded-md border-2 border-[--color-primary] bg-[--color-primary]/10 px-3 py-1.5 text-center min-w-[6rem] hover:bg-[--color-primary]/20 transition-colors"
          >
            <p className="font-mono font-bold text-base tracking-widest text-[--color-primary]">
              {vei.placa}
            </p>
            {vei.tipo && (
              <p className="text-[10px] uppercase tracking-wide text-[--color-text-muted] mt-0.5">{vei.tipo}</p>
            )}
          </Link>
        ) : (
          <div className="shrink-0 rounded-md border-2 border-[--color-primary] bg-[--color-primary]/10 px-3 py-1.5 text-center min-w-[6rem]">
            <p className="font-mono font-bold text-base tracking-widest text-[--color-primary]">—</p>
          </div>
        )}

        {/* Detalhes */}
        <div className="space-y-0.5">
          <p className="text-sm font-semibold text-[--color-text-primary]">
            {[vei?.marca, vei?.modelo].filter(Boolean).join(" ") || "Veículo sem dados"}
          </p>
          <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-[--color-text-secondary]">
            {anoLabel && <span>{anoLabel}</span>}
            {vei?.cor && <span>{vei.cor}</span>}
          </div>
          <p className="text-xs text-[--color-text-muted] pt-1">
            Vinculado em {new Date(v.data_inicio).toLocaleDateString("pt-BR")}
            {v.data_fim && ` · até ${new Date(v.data_fim).toLocaleDateString("pt-BR")}`}
          </p>
        </div>
      </div>

      <div className="flex flex-col items-end gap-2 shrink-0">
        <Badge variant={v.ativo ? "success" : "secondary"} className="text-xs">
          {v.ativo ? "Ativo" : "Encerrado"}
        </Badge>
        {v.ativo && (
          <button
            type="button"
            onClick={onDesassociar}
            className="text-xs text-[--color-error] hover:underline"
          >
            Desassociar
          </button>
        )}
      </div>
    </div>
  );
}

function ClienteDetalhe() {
  const { clienteId } = Route.useParams();
  const queryClient = useQueryClient();
  const [showVincular, setShowVincular] = useState(false);

  const { data: cliente, isLoading } = useQuery({
    queryKey: ["cliente", clienteId],
    queryFn: () => api.get<Cliente>(`/clientes/${clienteId}`),
  });

  const { data: veiculos, isLoading: loadingVeiculos } = useQuery({
    queryKey: ["cliente-veiculos", clienteId],
    queryFn: () => api.get<ClienteVeiculo[]>(`/clientes/${clienteId}/veiculos`),
  });

  const desassociar = useMutation({
    mutationFn: (veiculoId: string) => api.delete(`/clientes/${clienteId}/veiculos/${veiculoId}`),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["cliente-veiculos", clienteId] }),
  });

  const ativos   = veiculos?.filter((v) => v.ativo) ?? [];
  const inativos = veiculos?.filter((v) => !v.ativo) ?? [];

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Link to="/app/clientes" className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary]">
          ← Clientes
        </Link>
      </div>

      {/* Dados do cliente */}
      <Card>
        <CardHeader className="flex flex-row items-start justify-between">
          <div>
            {isLoading ? (
              <Skeleton className="h-7 w-56 mb-1" />
            ) : (
              <>
                <CardTitle className="text-xl">{cliente?.nome}</CardTitle>
                {cliente?.apelido && (
                  <p className="text-sm text-[--color-text-muted] mt-0.5">"{cliente.apelido}"</p>
                )}
              </>
            )}
          </div>
          {!isLoading && cliente && (
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant={cliente.tipo_pessoa === "Juridica" ? "secondary" : "default"}>
                {cliente.tipo_pessoa === "Juridica" ? "Jurídica" : "Física"}
              </Badge>
              <Badge variant={cliente.ativo ? "success" : "secondary"}>
                {cliente.ativo ? "Ativo" : "Inativo"}
              </Badge>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-4 w-full" />)}
            </div>
          ) : (
            <div className="space-y-5">
              {/* Identificação */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-2">
                  Identificação
                </p>
                <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3">
                  <Campo label="CPF/CNPJ" value={cliente?.cpf_cnpj} />
                  <Campo label="RG" value={cliente?.rg} />
                  <Campo label="Sexo" value={cliente?.sexo} />
                </dl>
              </div>

              {/* Contato */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-2">
                  Contato
                </p>
                <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3">
                  <Campo label="Telefone" value={cliente?.telefone} />
                  <Campo label="Celular" value={cliente?.celular} />
                  <Campo label="E-mail" value={cliente?.email} />
                </dl>
              </div>

              {/* Endereço */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-2">
                  Endereço
                </p>
                <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3">
                  <Campo label="Endereço" value={cliente?.endereco} />
                  <Campo label="CEP" value={cliente?.cep} />
                  <Campo label="Cidade/UF" value={cliente?.cidade && cliente?.uf ? `${cliente.cidade}/${cliente.uf}` : (cliente?.cidade ?? cliente?.uf ?? null)} />
                </dl>
              </div>

              {/* Fiscal */}
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-2">
                  Fiscal
                </p>
                <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-6 gap-y-3">
                  <Campo label="Inscrição Estadual" value={cliente?.inscricao_estadual} />
                  <Campo label="Indicador IE" value={cliente?.indicador_ie} />
                  <Campo label="Consumidor Final" value={cliente?.consumidor_final ? "Sim" : "Não"} />
                </dl>
              </div>

              {/* Observações */}
              {cliente?.observacoes && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] mb-1">
                    Observações
                  </p>
                  <p className="text-sm text-[--color-text-secondary] whitespace-pre-wrap">{cliente.observacoes}</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Veículos */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>
            Veículos
            {!loadingVeiculos && veiculos && (
              <span className="ml-2 text-sm font-normal text-[--color-text-muted]">
                ({ativos.length} ativo{ativos.length !== 1 ? "s" : ""})
              </span>
            )}
          </CardTitle>
          <Button size="sm" variant="outline" onClick={() => setShowVincular((v) => !v)}>
            {showVincular ? "Cancelar" : "+ Vincular"}
          </Button>
        </CardHeader>
        <CardContent>
          {showVincular && (
            <VincularVeiculoForm clienteId={clienteId} onClose={() => setShowVincular(false)} />
          )}

          {loadingVeiculos ? (
            <div className="space-y-3 mt-4">
              <Skeleton className="h-20 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : veiculos?.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-6 text-center">
              Nenhum veículo vinculado.
            </p>
          ) : (
            <div className="space-y-3 mt-4">
              {ativos.map((v) => (
                <VeiculoCard
                  key={v.id}
                  v={v}
                  onDesassociar={() => desassociar.mutate(v.veiculo_id)}
                />
              ))}
              {inativos.length > 0 && (
                <>
                  <p className="text-xs font-semibold uppercase tracking-wide text-[--color-text-muted] pt-2">
                    Histórico
                  </p>
                  {inativos.map((v) => (
                    <VeiculoCard key={v.id} v={v} onDesassociar={() => {}} />
                  ))}
                </>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
