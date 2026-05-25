import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/os/")({
  component: OSPage,
});

interface OS {
  id: string;
  numero_os: string;
  status: string;
  cliente_nome: string | null;
  veiculo_placa: string | null;
  descricao_problema: string;
  total_final: string;
  aberta_em: string;
  fechada_em: string | null;
}

const STATUS_BADGE: Record<string, "default" | "warning" | "error" | "success" | "outline"> = {
  ABERTA: "default",
  EM_EXECUCAO: "warning",
  AGUARDANDO_PECA: "error",
  FECHADA: "success",
  CANCELADA: "error",
};

const STATUS_LABEL: Record<string, string> = {
  ABERTA: "Aberta",
  EM_EXECUCAO: "Em execução",
  AGUARDANDO_PECA: "Aguardando peça",
  FECHADA: "Fechada",
  CANCELADA: "Cancelada",
};

const FILTROS = ["Todas", "ABERTA", "EM_EXECUCAO", "AGUARDANDO_PECA", "FECHADA"] as const;

function OSPage() {
  const [filtro, setFiltro] = useState<string>("Todas");
  const [placaInput, setPlacaInput] = useState("");
  const [placa, setPlaca] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["os", filtro, placa],
    queryFn: () => {
      const params = new URLSearchParams();
      if (filtro !== "Todas") params.set("status_os", filtro);
      if (placa) params.set("placa", placa);
      const qs = params.toString();
      return api.get<{ total: number; items: OS[] }>(`/os${qs ? `?${qs}` : ""}`);
    },
  });

  const items = data?.items ?? [];

  function handleBuscarPlaca(e: FormEvent) {
    e.preventDefault();
    const p = placaInput.trim().toUpperCase();
    setPlaca(p);
    if (p) setFiltro("Todas");
  }

  function limparPlaca() {
    setPlaca("");
    setPlacaInput("");
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Ordens de Serviço</h1>
        <Link to="/app/os/nova" search={{}}>
          <Button size="sm">+ Nova OS</Button>
        </Link>
      </div>

      {/* ── Busca por placa ─────────────────────────────────────────────── */}
      <form onSubmit={handleBuscarPlaca} className="flex gap-2 items-center">
        <input
          value={placaInput}
          onChange={(e) => setPlacaInput(e.target.value.toUpperCase())}
          placeholder="Buscar por placa…"
          maxLength={8}
          className="w-40 rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <Button type="submit" size="sm" disabled={placaInput.trim().length < 7}>
          Buscar
        </Button>
        {placa && (
          <button
            type="button"
            onClick={limparPlaca}
            className="text-xs text-[--color-text-muted] hover:text-[--color-error]"
          >
            Limpar
          </button>
        )}
        {placa && (
          <span className="text-sm text-[--color-text-muted]">
            Placa:{" "}
            <span className="font-mono font-medium text-[--color-text-primary]">{placa}</span>
          </span>
        )}
      </form>

      {/* ── Filtros de status ────────────────────────────────────────────── */}
      {!placa && (
        <div className="flex gap-1 flex-wrap">
          {FILTROS.map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFiltro(f)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filtro === f
                  ? "bg-[--color-primary] text-[--color-primary-fg]"
                  : "bg-[var(--color-background)] text-[--color-text-secondary] hover:text-[--color-text-primary]"
              }`}
            >
              {f === "Todas" ? "Todas" : STATUS_LABEL[f]}
            </button>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : items.length === 0 ? (
            <p className="text-sm text-[--color-text-muted] py-8 text-center">
              {placa ? `Nenhuma OS encontrada para a placa ${placa}.` : "Nenhuma OS encontrada."}
            </p>
          ) : (
            items.map((os) => (
              <Link
                key={os.id}
                to="/app/os/$osId"
                params={{ osId: os.id }}
                className="block px-4 py-3 border-b border-[--color-border] last:border-0 hover:bg-[var(--color-background)] transition-colors"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-[--color-text-primary]">
                        {os.numero_os}
                      </span>
                      <Badge variant={STATUS_BADGE[os.status] ?? "outline"}>
                        {STATUS_LABEL[os.status] ?? os.status}
                      </Badge>
                      {os.veiculo_placa && (
                        <span className="text-xs font-mono text-[--color-text-muted] bg-[var(--color-background)] px-1.5 py-0.5 rounded">
                          {os.veiculo_placa}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-[--color-text-muted] mt-0.5 truncate">
                      {os.cliente_nome ?? "Cliente não identificado"}
                      {" · "}
                      {os.descricao_problema}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm font-mono font-semibold text-[--color-text-primary]">
                      {Number(os.total_final).toLocaleString("pt-BR", {
                        style: "currency",
                        currency: "BRL",
                      })}
                    </p>
                    <p className="text-xs text-[--color-text-muted]">
                      {new Date(os.aberta_em).toLocaleDateString("pt-BR")}
                    </p>
                  </div>
                </div>
              </Link>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
