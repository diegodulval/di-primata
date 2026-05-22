import { formatDateTime } from "@di-mata/shared";
import { Badge } from "@di-mata/ui";
import { Card, CardContent } from "@di-mata/ui";
import { Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/registros/")({
  component: RegistrosPage,
});

const ATIVIDADE_LABEL: Record<string, string> = {
  adubacao: "Adubação",
  irrigacao: "Irrigação",
  colheita: "Colheita",
  poda: "Poda",
  pulverizacao: "Pulverização",
};

type Registro = {
  id: string;
  phone: string | null;
  profile_name: string | null;
  propriedade: string | null;
  talhao: string | null;
  atividade: string;
  valor_gasto: number | null;
  capturado_em: string;
  ciclo_id: string;
};

function useRegistros() {
  return useQuery<Registro[]>({
    queryKey: ["registros"],
    queryFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const res = await fetch("/api/whatsapp/registros", {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) throw new Error("Erro ao carregar registros");
      return res.json();
    },
    refetchInterval: 15_000,
  });
}

function formatValor(valor: number | null) {
  if (valor == null) return "—";
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function AtividadeBadge({ atividade }: { atividade: string }) {
  const label = ATIVIDADE_LABEL[atividade] ?? atividade;
  return <Badge variant="outline">{label}</Badge>;
}

function RegistrosPage() {
  const { data: registros, isLoading, isError } = useRegistros();

  return (
    <div className="p-6 space-y-6">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[--color-text-primary]">Registros</h1>
          <p className="text-sm text-[--color-text-muted] mt-1">
            Atividades registradas via WhatsApp — atualiza a cada 15s
          </p>
        </div>
        {registros && (
          <span className="text-sm text-[--color-text-muted]">
            {registros.length} registro{registros.length !== 1 ? "s" : ""}
          </span>
        )}
      </header>

      {isError && <p className="text-sm text-[--color-error]">Erro ao carregar registros.</p>}

      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      )}

      {registros && registros.length === 0 && (
        <Card>
          <CardContent className="py-10 text-center text-[--color-text-muted] text-sm">
            Nenhum registro ainda. As atividades enviadas via WhatsApp aparecerão aqui.
          </CardContent>
        </Card>
      )}

      {registros && registros.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[--color-border]">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-[--color-surface] border-b border-[--color-border]">
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Produtor
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Propriedade
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Talhão
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">
                  Atividade
                </th>
                <th className="px-4 py-3 text-right font-medium text-[--color-text-muted]">
                  Valor
                </th>
                <th className="px-4 py-3 text-left font-medium text-[--color-text-muted]">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[--color-border]">
              {registros.map((r) => (
                <tr
                  key={r.id}
                  className="bg-[--color-surface] hover:bg-[--color-background] transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs text-[--color-text-primary]">
                      {r.phone ?? "—"}
                    </div>
                    {r.profile_name && (
                      <div className="text-xs text-[--color-text-muted] mt-0.5">
                        {r.profile_name}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-[--color-text-secondary]">
                    {r.propriedade ?? <span className="text-[--color-text-muted]">—</span>}
                  </td>
                  <td className="px-4 py-3 text-[--color-text-secondary]">
                    {r.talhao ?? <span className="text-[--color-text-muted]">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <AtividadeBadge atividade={r.atividade} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-[--color-text-primary]">
                    {formatValor(r.valor_gasto)}
                  </td>
                  <td className="px-4 py-3 text-[--color-text-muted] whitespace-nowrap">
                    {formatDateTime(r.capturado_em)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
