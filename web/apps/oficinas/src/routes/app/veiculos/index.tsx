import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { type FormEvent, useState } from "react";

export const Route = createFileRoute("/app/veiculos/")({
  component: VeiculosPage,
});

interface HistoricoItem {
  id: string;
  data_servico: string;
  km_entrada: number | null;
  resumo_publico: string | null;
}

interface VeiculoDetalhe {
  id: string;
  placa: string;
  marca: string | null;
  modelo: string | null;
  ano_fab: number | null;
  ano_mod: number | null;
  cor: string | null;
  tipo: string | null;
  historico_publico: HistoricoItem[];
}

function VeiculosPage() {
  const [placa, setPlaca] = useState("");
  const [query, setQuery] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["veiculo", query],
    queryFn: async () => {
      if (!query) return null;
      setNotFound(false);
      try {
        return await api.get<VeiculoDetalhe>(`/veiculos/${encodeURIComponent(query)}`);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setNotFound(true);
          return null;
        }
        throw err;
      }
    },
    enabled: query !== null,
  });

  function handleSearch(e: FormEvent) {
    e.preventDefault();
    const normalized = placa.trim().toUpperCase();
    if (normalized) setQuery(normalized);
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-6">Veículos</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <input
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC1234 ou ABC1D23"
          maxLength={8}
          className="rounded-md border border-[--color-border] bg-[--color-surface] px-3 py-2 text-sm font-mono uppercase w-48 focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <Button type="submit" disabled={isLoading}>
          {isLoading ? "Buscando..." : "Buscar"}
        </Button>
      </form>

      {notFound && (
        <p className="text-sm text-[--color-text-muted]">
          Veículo com placa <strong>{query}</strong> não encontrado no cadastro.
        </p>
      )}

      {data && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <CardTitle className="font-mono text-xl">{data.placa}</CardTitle>
                {data.tipo && <Badge variant="outline">{data.tipo}</Badge>}
              </div>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-3 text-sm">
                <div>
                  <dt className="text-[--color-text-muted]">Marca</dt>
                  <dd className="text-[--color-text-primary]">{data.marca ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-[--color-text-muted]">Modelo</dt>
                  <dd className="text-[--color-text-primary]">{data.modelo ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-[--color-text-muted]">Cor</dt>
                  <dd className="text-[--color-text-primary]">{data.cor ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-[--color-text-muted]">Ano fab.</dt>
                  <dd className="text-[--color-text-primary]">{data.ano_fab ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-[--color-text-muted]">Ano mod.</dt>
                  <dd className="text-[--color-text-primary]">{data.ano_mod ?? "—"}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          {data.historico_publico.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Histórico público</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {data.historico_publico.map((h) => (
                    <div key={h.id} className="text-sm border-l-2 border-[--color-primary] pl-3">
                      <p className="font-medium text-[--color-text-primary]">
                        {h.data_servico}
                        {h.km_entrada != null && (
                          <span className="font-normal text-[--color-text-muted] ml-2">
                            {h.km_entrada.toLocaleString()} km
                          </span>
                        )}
                      </p>
                      {h.resumo_publico && (
                        <p className="text-[--color-text-secondary] mt-0.5">{h.resumo_publico}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
