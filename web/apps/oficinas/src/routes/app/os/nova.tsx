import { ApiError, api } from "@/lib/api";
import { Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { type FormEvent, useEffect, useState } from "react";

export const Route = createFileRoute("/app/os/nova")({
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

interface OS {
  id: string;
}

const TIPOS_VEICULO = ["carro", "moto", "caminhao", "van"] as const;

function NovaOSPage() {
  const navigate = useNavigate();

  // ── 1. Veículo ────────────────────────────────────────────────────────────
  const [placaInput, setPlacaInput] = useState("");
  const [placaBusca, setPlacaBusca] = useState("");
  const [veiculoEncontrado, setVeiculoEncontrado] = useState<Veiculo | null>(null);
  const [veiculoNaoEncontrado, setVeiculoNaoEncontrado] = useState(false);
  const [criandoVeiculo, setCriandoVeiculo] = useState(false);
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
      setClienteSelecionado(null);
      setClienteAutoFetch(false);
      try {
        return await api.get<Veiculo>(`/veiculos/${encodeURIComponent(placa)}`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setVeiculoNaoEncontrado(true);
          return null;
        }
        throw err;
      }
    },
    onSuccess: (v) => {
      if (v) setVeiculoEncontrado(v);
    },
  });

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
          {veiculoEncontrado ? (
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
                  setClienteSelecionado(null);
                  setClienteAutoFetch(false);
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
                  <p className="text-xs font-medium text-[--color-text-muted]">
                    Novo veículo —{" "}
                    <span className="font-mono text-[--color-text-primary]">{placaBusca}</span>
                  </p>
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
                      onClick={() => setCriandoVeiculo(false)}
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
