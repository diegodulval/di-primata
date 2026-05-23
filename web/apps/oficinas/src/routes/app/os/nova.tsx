import { ApiError, api } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/app/os/nova")({
  validateSearch: (search: Record<string, unknown>): { cliente_id?: string; placa?: string } => ({
    ...(typeof search.cliente_id === "string" && { cliente_id: search.cliente_id }),
    ...(typeof search.placa === "string" && { placa: search.placa }),
  }),
  component: NovaOSPage,
});

interface Cliente {
  id: string;
  nome: string;
  telefone: string | null;
  cpf_cnpj: string | null;
}

interface Veiculo {
  id: string;
  placa: string;
  marca: string | null;
  modelo: string | null;
  tipo: string | null;
}

interface ConsultaVeiculo {
  fonte: "db" | "sinesp" | "nao_encontrado";
  id: string | null;
  placa: string;
  marca: string | null;
  modelo: string | null;
  ano_fab: number | null;
  ano_mod: number | null;
  cor: string | null;
  tipo: string | null;
  municipio: string | null;
  uf: string | null;
  situacao: string | null;
}

interface OS {
  id: string;
}

interface ClienteVeiculoLink {
  id: string;
  ativo: boolean;
  veiculo: { placa: string; marca: string | null; modelo: string | null; ano_fab: number | null; tipo: string | null } | null;
}

const TIPOS_VEICULO = ["carro", "moto", "caminhao", "van"] as const;

function NovaOSPage() {
  const navigate = useNavigate();
  const { cliente_id: clienteIdParam, placa: placaParam } = Route.useSearch();

  // ── 1. Veículo ────────────────────────────────────────────────────────────
  const preserveCliente = useRef(false);
  const [showVehiclePicker, setShowVehiclePicker] = useState(false);
  const [placaInput, setPlacaInput] = useState(placaParam ?? "");
  const [placaBusca, setPlacaBusca] = useState(placaParam ?? "");
  const [veiculoEncontrado, setVeiculoEncontrado] = useState<Veiculo | null>(null);
  const [veiculoNaoEncontrado, setVeiculoNaoEncontrado] = useState(false);
  const [criandoVeiculo, setCriandoVeiculo] = useState(false);
  const [sinespPreenchido, setSinespPreenchido] = useState(false);
  const [sinespSituacao, setSinespSituacao] = useState<string | null>(null);
  const [vMarca, setVMarca] = useState("");
  const [vModelo, setVModelo] = useState("");
  const [vAnoFab, setVAnoFab] = useState("");
  const [vAnoMod, setVAnoMod] = useState("");
  const [vCor, setVCor] = useState("");
  const [vTipo, setVTipo] = useState<(typeof TIPOS_VEICULO)[number] | "">("");

  // ── 2. Cliente ────────────────────────────────────────────────────────────
  const [clienteSelecionado, setClienteSelecionado] = useState<Cliente | null>(null);
  const [clienteAutoFetch, setClienteAutoFetch] = useState(false);
  const [qCliente, setQCliente] = useState("");
  const [buscaCliente, setBuscaCliente] = useState("");

  // ── 3. Detalhes ───────────────────────────────────────────────────────────
  const [km, setKm] = useState("");
  const [descricao, setDescricao] = useState("");
  const [erro, setErro] = useState<string | null>(null);

  // ── Pre-preenche cliente vindo da listagem ────────────────────────────────
  const { data: clienteParam } = useQuery({
    queryKey: ["cliente-pre-os", clienteIdParam],
    queryFn: () => api.get<Cliente>(`/clientes/${clienteIdParam}`),
    enabled: !!clienteIdParam,
  });

  useEffect(() => {
    if (clienteParam && !clienteSelecionado) {
      setClienteSelecionado(clienteParam);
    }
  }, [clienteParam, clienteSelecionado]);

  // ── Auto-fetch do dono do veículo ao confirmar placa ──────────────────────
  const { data: clienteAtual, isLoading: carregandoCliente } = useQuery({
    queryKey: ["veiculo-cliente-atual", veiculoEncontrado?.placa],
    queryFn: async () => {
      try {
        const placa = veiculoEncontrado?.placa;
        if (!placa) return null;
        return await api.get<Cliente>(`/veiculos/${encodeURIComponent(placa)}/cliente-atual`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
    enabled: !!veiculoEncontrado && !clienteSelecionado,
  });

  useEffect(() => {
    if (clienteAtual && !clienteSelecionado) {
      setClienteSelecionado(clienteAtual);
      setClienteAutoFetch(true);
    }
  }, [clienteAtual, clienteSelecionado]);

  // ── Busca manual de clientes ──────────────────────────────────────────────
  const { data: clientesResult } = useQuery({
    queryKey: ["clientes-busca", buscaCliente],
    queryFn: () => api.get<{ items: Cliente[] }>(`/clientes?q=${encodeURIComponent(buscaCliente)}`),
    enabled: buscaCliente.trim().length >= 2,
  });
  const clientes = clientesResult?.items ?? [];

  function handleBuscarCliente(e: FormEvent) {
    e.preventDefault();
    setBuscaCliente(qCliente.trim());
  }

  // ── Busca de veículo por placa ────────────────────────────────────────────
  const buscarVeiculo = useMutation({
    mutationFn: async (placa: string) => {
      setVeiculoNaoEncontrado(false);
      setVeiculoEncontrado(null);
      setSinespPreenchido(false);
      setSinespSituacao(null);
      if (!preserveCliente.current) {
        setClienteSelecionado(null);
        setClienteAutoFetch(false);
      }
      preserveCliente.current = false;
      return api.get<ConsultaVeiculo>(`/veiculos/${encodeURIComponent(placa)}/consultar`);
    },
    onSuccess: (res) => {
      if (res.fonte === "db" && res.id) {
        setVeiculoEncontrado({ id: res.id, placa: res.placa, marca: res.marca, modelo: res.modelo, tipo: res.tipo });
      } else if (res.fonte === "sinesp") {
        // Pré-preenche o form com os dados do SINESP
        setVMarca(res.marca ?? "");
        setVModelo(res.modelo ?? "");
        setVAnoFab(res.ano_fab != null ? String(res.ano_fab) : "");
        setVAnoMod(res.ano_mod != null ? String(res.ano_mod) : "");
        setVCor(res.cor ?? "");
        setSinespPreenchido(true);
        setSinespSituacao(res.situacao);
        setVeiculoNaoEncontrado(true);
        setCriandoVeiculo(true);
      } else {
        setVeiculoNaoEncontrado(true);
      }
    },
  });

  // Dispara busca automática quando placa veio via search param
  const placaParamSearched = useRef(false);
  useEffect(() => {
    if (placaParam && !placaParamSearched.current) {
      placaParamSearched.current = true;
      buscarVeiculo.mutate(placaParam);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Veículos do cliente para picker ──────────────────────────────────────
  const { data: clienteVeiculos } = useQuery({
    queryKey: ["cliente-veiculos-os", clienteIdParam],
    queryFn: () => api.get<ClienteVeiculoLink[]>(`/clientes/${clienteIdParam}/veiculos`),
    enabled: !!clienteIdParam && !placaParam,
  });

  const veiculosAtivos = (clienteVeiculos ?? []).filter((v) => v.ativo && v.veiculo?.placa);

  useEffect(() => {
    if (!clienteVeiculos || veiculoEncontrado) return;
    if (veiculosAtivos.length === 1) {
      const [primeiro] = veiculosAtivos;
      const placa = primeiro?.veiculo?.placa;
      if (!placa) return;
      setPlacaInput(placa);
      setPlacaBusca(placa);
      preserveCliente.current = true;
      buscarVeiculo.mutate(placa);
    } else if (veiculosAtivos.length > 1) {
      setShowVehiclePicker(true);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteVeiculos]);

  function handleBuscarPlaca(e: FormEvent) {
    e.preventDefault();
    const p = placaInput.trim().toUpperCase();
    if (p) {
      setPlacaBusca(p);
      buscarVeiculo.mutate(p);
    }
  }

  // ── Criar veículo inline ──────────────────────────────────────────────────
  const criarVeiculo = useMutation({
    mutationFn: () =>
      api.post<Veiculo>("/veiculos", {
        placa: placaBusca,
        marca: vMarca || null,
        modelo: vModelo || null,
        ano_fab: vAnoFab ? Number(vAnoFab) : null,
        ano_mod: vAnoMod ? Number(vAnoMod) : null,
        cor: vCor || null,
        tipo: vTipo || null,
      }),
    onSuccess: (v) => {
      setVeiculoEncontrado(v);
      setVeiculoNaoEncontrado(false);
      setCriandoVeiculo(false);
    },
    onError: (err: Error) => setErro(err.message),
  });

  // ── Criar OS ──────────────────────────────────────────────────────────────
  const criarOS = useMutation({
    mutationFn: () =>
      api.post<OS>("/os", {
        cliente_id: clienteSelecionado?.id,
        veiculo_id: veiculoEncontrado?.id,
        km_entrada: km ? Number(km) : null,
        descricao_problema: descricao,
      }),
    onSuccess: (os) => void navigate({ to: "/app/os/$osId", params: { osId: os.id } }),
    onError: (err: Error) => setErro(err.message),
  });

  const podeSalvar = !!clienteSelecionado && !!veiculoEncontrado && descricao.trim().length > 0;

  return (
    <div className="p-8 space-y-6 max-w-2xl">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Nova OS</h1>
        <Button size="sm" variant="outline" onClick={() => void navigate({ to: "/app/os" })}>
          Cancelar
        </Button>
      </div>

      {/* ── 1. Veículo ────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>1. Veículo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {showVehiclePicker && !veiculoEncontrado ? (
            <div className="space-y-2">
              <p className="text-xs text-[--color-text-muted] mb-3">
                O cliente tem {veiculosAtivos.length} veículos. Selecione qual será usado na OS:
              </p>
              {veiculosAtivos.map((v) => (
                <button
                  key={v.id}
                  type="button"
                  onClick={() => {
                    const placa = v.veiculo!.placa;
                    setPlacaInput(placa);
                    setPlacaBusca(placa);
                    setShowVehiclePicker(false);
                    preserveCliente.current = true;
                    buscarVeiculo.mutate(placa);
                  }}
                  className="w-full flex items-center gap-3 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2.5 text-left hover:border-[--color-primary] hover:bg-[--color-primary]/5 transition-colors"
                >
                  <span className="font-mono font-bold text-sm tracking-widest text-[--color-primary] shrink-0">
                    {v.veiculo?.placa}
                  </span>
                  <span className="text-sm text-[--color-text-secondary]">
                    {[v.veiculo?.marca, v.veiculo?.modelo, v.veiculo?.ano_fab].filter(Boolean).join(" ")}
                    {v.veiculo?.tipo && (
                      <span className="ml-1 text-xs text-[--color-text-muted] uppercase">{v.veiculo.tipo}</span>
                    )}
                  </span>
                </button>
              ))}
              <button
                type="button"
                onClick={() => setShowVehiclePicker(false)}
                className="text-xs text-[--color-text-muted] hover:text-[--color-text-primary] pt-1"
              >
                Buscar outra placa →
              </button>
            </div>
          ) : veiculoEncontrado ? (
            <div className="flex items-center justify-between rounded-md border border-[--color-border] px-3 py-2">
              <div>
                <p className="text-sm font-medium font-mono text-[--color-text-primary]">
                  {veiculoEncontrado.placa}
                </p>
                <p className="text-xs text-[--color-text-muted]">
                  {[veiculoEncontrado.marca, veiculoEncontrado.modelo, veiculoEncontrado.tipo]
                    .filter(Boolean)
                    .join(" · ")}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setVeiculoEncontrado(null);
                  setVeiculoNaoEncontrado(false);
                  setPlacaInput("");
                  setCriandoVeiculo(false);
                  if (veiculosAtivos.length > 1) {
                    setShowVehiclePicker(true);
                  } else {
                    setClienteSelecionado(null);
                    setClienteAutoFetch(false);
                  }
                }}
                className="text-xs text-[--color-text-muted] hover:text-[--color-error]"
              >
                Trocar
              </button>
            </div>
          ) : (
            <>
              <form onSubmit={handleBuscarPlaca} className="flex gap-2">
                <input
                  value={placaInput}
                  onChange={(e) => setPlacaInput(e.target.value.toUpperCase())}
                  placeholder="ABC1234"
                  maxLength={8}
                  className="w-36 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={placaInput.trim().length < 7 || buscarVeiculo.isPending}
                >
                  {buscarVeiculo.isPending ? "Buscando..." : "Buscar placa"}
                </Button>
              </form>

              {veiculoNaoEncontrado && !criandoVeiculo && (
                <div className="flex items-center gap-3">
                  <p className="text-sm text-[--color-text-muted]">
                    Placa <strong>{placaBusca}</strong> não cadastrada.
                  </p>
                  <Button size="sm" variant="outline" onClick={() => setCriandoVeiculo(true)}>
                    Cadastrar
                  </Button>
                </div>
              )}

              {criandoVeiculo && (
                <div className="border border-[--color-border] rounded-md p-3 space-y-3">
                  <div className="flex items-center justify-between flex-wrap gap-2">
                    <p className="text-xs font-medium text-[--color-text-muted]">
                      Novo veículo —{" "}
                      <span className="font-mono text-[--color-text-primary]">{placaBusca}</span>
                    </p>
                    {sinespPreenchido && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-[--color-primary]/10 px-2 py-0.5 text-[11px] font-medium text-[--color-primary]">
                        Dados do SINESP{sinespSituacao ? ` · ${sinespSituacao}` : ""}
                      </span>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {(
                      [
                        ["v-marca", "Marca", vMarca, setVMarca, "Toyota"],
                        ["v-modelo", "Modelo", vModelo, setVModelo, "Corolla"],
                        ["v-anofab", "Ano fab.", vAnoFab, setVAnoFab, "2020"],
                        ["v-anomod", "Ano mod.", vAnoMod, setVAnoMod, "2021"],
                        ["v-cor", "Cor", vCor, setVCor, "Prata"],
                      ] as [string, string, string, (v: string) => void, string][]
                    ).map(([id, label, val, setter, ph]) => (
                      <div key={id} className="space-y-0.5">
                        <label htmlFor={id} className="text-xs text-[--color-text-muted]">
                          {label}
                        </label>
                        <input
                          id={id}
                          value={val}
                          onChange={(e) => setter(e.target.value)}
                          placeholder={ph}
                          className="w-full rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                        />
                      </div>
                    ))}
                    <div className="space-y-0.5">
                      <label htmlFor="v-tipo" className="text-xs text-[--color-text-muted]">
                        Tipo
                      </label>
                      <select
                        id="v-tipo"
                        value={vTipo}
                        onChange={(e) =>
                          setVTipo(e.target.value as (typeof TIPOS_VEICULO)[number] | "")
                        }
                        className="w-full rounded border border-[--color-border] bg-[--color-surface] px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                      >
                        <option value="">Selecione</option>
                        {TIPOS_VEICULO.map((t) => (
                          <option key={t} value={t}>
                            {t}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="flex gap-2 justify-end">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setCriandoVeiculo(false);
                        setSinespPreenchido(false);
                        setSinespSituacao(null);
                        setVMarca(""); setVModelo(""); setVAnoFab(""); setVAnoMod(""); setVCor("");
                      }}
                    >
                      Cancelar
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      disabled={criarVeiculo.isPending}
                      onClick={() => criarVeiculo.mutate()}
                    >
                      {criarVeiculo.isPending ? "Salvando..." : "Salvar veículo"}
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ── 2. Cliente ────────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>2. Cliente</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {clienteSelecionado ? (
            <div className="flex items-center justify-between rounded-md border border-[--color-border] px-3 py-2">
              <div>
                <p className="text-sm font-medium text-[--color-text-primary]">
                  {clienteSelecionado.nome}
                  {clienteAutoFetch && (
                    <span className="ml-2 text-xs font-normal text-[--color-text-muted]">
                      (dono do veículo)
                    </span>
                  )}
                </p>
                <p className="text-xs text-[--color-text-muted]">
                  {clienteSelecionado.telefone ?? clienteSelecionado.cpf_cnpj ?? ""}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setClienteSelecionado(null);
                  setClienteAutoFetch(false);
                  setQCliente("");
                  setBuscaCliente("");
                }}
                className="text-xs text-[--color-text-muted] hover:text-[--color-error]"
              >
                Trocar
              </button>
            </div>
          ) : carregandoCliente && veiculoEncontrado ? (
            <p className="text-sm text-[--color-text-muted]">Buscando dono do veículo...</p>
          ) : (
            <>
              {veiculoEncontrado && (
                <p className="text-xs text-[--color-text-muted]">
                  Nenhum cliente vinculado à placa{" "}
                  <span className="font-mono font-medium">{veiculoEncontrado.placa}</span>. Busque
                  abaixo.
                </p>
              )}
              <form onSubmit={handleBuscarCliente} className="flex gap-2">
                <input
                  value={qCliente}
                  onChange={(e) => setQCliente(e.target.value)}
                  placeholder="Buscar por nome, CPF ou telefone..."
                  className="flex-1 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
                <Button type="submit" size="sm" disabled={qCliente.trim().length < 2}>
                  Buscar
                </Button>
              </form>
              {clientes.length > 0 && (
                <div className="border border-[--color-border] rounded-md divide-y divide-[--color-border]">
                  {clientes.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => {
                        setClienteSelecionado(c);
                        setQCliente("");
                        setBuscaCliente("");
                      }}
                      className="w-full px-3 py-2 text-left hover:bg-[--color-background] transition-colors"
                    >
                      <p className="text-sm font-medium text-[--color-text-primary]">{c.nome}</p>
                      <p className="text-xs text-[--color-text-muted]">
                        {c.telefone ?? c.cpf_cnpj ?? ""}
                      </p>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* ── 3. Detalhes ───────────────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle>3. Detalhes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1">
            <label htmlFor="os-km" className="text-sm font-medium text-[--color-text-primary]">
              KM entrada
            </label>
            <input
              id="os-km"
              type="number"
              value={km}
              onChange={(e) => setKm(e.target.value)}
              placeholder="Ex: 45000"
              className="w-40 rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
            />
          </div>
          <div className="space-y-1">
            <label
              htmlFor="os-descricao"
              className="text-sm font-medium text-[--color-text-primary]"
            >
              Descrição do problema *
            </label>
            <textarea
              id="os-descricao"
              value={descricao}
              onChange={(e) => setDescricao(e.target.value)}
              rows={3}
              placeholder="Descreva o problema relatado pelo cliente..."
              className="w-full rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary] resize-none"
            />
          </div>
        </CardContent>
      </Card>

      {erro && <p className="text-sm text-[--color-error]">{erro}</p>}

      <div className="flex justify-end">
        <Button disabled={!podeSalvar || criarOS.isPending} onClick={() => criarOS.mutate()}>
          {criarOS.isPending ? "Abrindo OS..." : "Abrir OS"}
        </Button>
      </div>
    </div>
  );
}
