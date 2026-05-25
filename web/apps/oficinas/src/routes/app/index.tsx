import { api } from "@/lib/api";
import { Badge, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/")({
  component: HomePage,
});

interface OSRecenteItem {
  id: string;
  numero_os: string;
  placa: string;
  descricao_problema: string;
  status: string;
  mecanico_nome: string;
}

interface AniversarianteItem {
  id: string;
  nome: string;
  celular: string | null;
  telefone: string | null;
  data_nascimento: string;
}

interface DashboardData {
  os_abertas: number;
  os_em_execucao: number;
  os_aguardando_peca: number;
  os_fechadas_hoje: number;
  vendas_hoje: number;
  estoque_critico: number;
  faturamento_hoje: number;
  faturamento_mes: number;
  ticket_medio_os_mes: number;
  ticket_medio_venda_mes: number;
  aniversariantes_hoje: number;
  aniversariantes_semana: number;
  aniversariantes_hoje_lista: AniversarianteItem[];
  os_recentes: OSRecenteItem[];
}

const STATUS_BADGE: Record<string, "default" | "warning" | "error" | "success"> = {
  ABERTA: "default",
  EM_EXECUCAO: "warning",
  AGUARDANDO_PECA: "error",
};

const STATUS_LABEL: Record<string, string> = {
  ABERTA: "Aberta",
  EM_EXECUCAO: "Em execução",
  AGUARDANDO_PECA: "Ag. peça",
};

function brl(value: number) {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function KpiCard({
  title,
  value,
  sub,
  alert,
  loading,
}: {
  title: string;
  value: number | string;
  sub?: string;
  alert?: boolean;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[var(--color-text-muted)]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <div className="flex items-end gap-2">
            <p
              className={`text-3xl font-bold ${alert ? "text-[var(--color-error)]" : "text-[var(--color-text-primary)]"}`}
            >
              {value}
            </p>
            {sub && <p className="text-xs text-[var(--color-text-muted)] mb-1">{sub}</p>}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function FinCard({
  title,
  value,
  loading,
}: {
  title: string;
  value: number;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[var(--color-text-muted)]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-32" />
        ) : (
          <p className="text-2xl font-bold text-[var(--color-text-primary)]">{brl(value)}</p>
        )}
      </CardContent>
    </Card>
  );
}

function HomePage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api.get<DashboardData>("/me/dashboard"),
    refetchInterval: 60_000,
  });

  const osEmAberto = (data?.os_abertas ?? 0) + (data?.os_em_execucao ?? 0) + (data?.os_aguardando_peca ?? 0);

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Início</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">Visão geral da oficina</p>
      </div>

      {/* Operacional */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Operacional
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          <KpiCard title="OS em aberto" value={osEmAberto} loading={isLoading} />
          <KpiCard
            title="Em execução"
            value={data?.os_em_execucao ?? 0}
            loading={isLoading}
          />
          <KpiCard
            title="Ag. peça"
            value={data?.os_aguardando_peca ?? 0}
            loading={isLoading}
          />
          <KpiCard
            title="Fechadas hoje"
            value={data?.os_fechadas_hoje ?? 0}
            loading={isLoading}
          />
          <KpiCard
            title="Vendas hoje"
            value={data?.vendas_hoje ?? 0}
            loading={isLoading}
          />
          <KpiCard
            title="Estoque crítico"
            value={data?.estoque_critico ?? 0}
            alert={(data?.estoque_critico ?? 0) > 0}
            sub="produtos"
            loading={isLoading}
          />
        </div>
      </section>

      {/* Financeiro */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Financeiro
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <FinCard title="Faturamento hoje" value={data?.faturamento_hoje ?? 0} loading={isLoading} />
          <FinCard title="Faturamento do mês" value={data?.faturamento_mes ?? 0} loading={isLoading} />
          <FinCard
            title="Ticket médio OS (mês)"
            value={data?.ticket_medio_os_mes ?? 0}
            loading={isLoading}
          />
          <FinCard
            title="Ticket médio venda (mês)"
            value={data?.ticket_medio_venda_mes ?? 0}
            loading={isLoading}
          />
        </div>
      </section>

      {/* Aniversariantes */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          Aniversariantes
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            title="Aniversariantes hoje"
            value={data?.aniversariantes_hoje ?? 0}
            alert={(data?.aniversariantes_hoje ?? 0) > 0}
            loading={isLoading}
          />
          <KpiCard
            title="Aniversariantes na semana"
            value={data?.aniversariantes_semana ?? 0}
            loading={isLoading}
          />
        </div>
        {(data?.aniversariantes_hoje_lista.length ?? 0) > 0 && (
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)]">Nome</th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)] hidden sm:table-cell">Celular</th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)] hidden sm:table-cell">Telefone</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data!.aniversariantes_hoje_lista.map((a, idx) => (
                      <tr
                        key={a.id}
                        className={`border-b border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-background)] transition-colors ${idx === data!.aniversariantes_hoje_lista.length - 1 ? "border-b-0" : ""}`}
                      >
                        <td className="px-4 py-3 font-medium">
                          <Link
                            to="/app/clientes"
                            className="text-[var(--color-primary)] hover:underline"
                          >
                            {a.nome}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-[var(--color-text-muted)] hidden sm:table-cell">
                          {a.celular ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-[var(--color-text-muted)] hidden sm:table-cell">
                          {a.telefone ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}
      </section>

      {/* OS em andamento */}
      <section className="space-y-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
          OS em andamento
        </h2>
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-3">
                {[...Array(3)].map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : !data?.os_recentes.length ? (
              <p className="text-sm text-[var(--color-text-muted)] p-6 text-center">
                Nenhuma OS em aberto no momento.
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)] bg-[var(--color-surface)]">
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)]">Nº OS</th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)]">Placa</th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)] hidden md:table-cell">
                        Problema
                      </th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)] hidden sm:table-cell">
                        Mecânico
                      </th>
                      <th className="text-left px-4 py-3 font-medium text-[var(--color-text-muted)]">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.os_recentes.map((os, idx) => (
                      <tr
                        key={os.id}
                        className={`border-b border-[var(--color-border)] bg-[var(--color-surface)] hover:bg-[var(--color-background)] transition-colors ${idx === data.os_recentes.length - 1 ? "border-b-0" : ""}`}
                      >
                        <td className="px-4 py-3 font-medium">
                          <Link
                            to="/app/os/$osId"
                            params={{ osId: os.id }}
                            className="text-[var(--color-primary)] hover:underline"
                          >
                            {os.numero_os}
                          </Link>
                        </td>
                        <td className="px-4 py-3 font-mono">{os.placa}</td>
                        <td className="px-4 py-3 text-[var(--color-text-muted)] hidden md:table-cell max-w-xs truncate">
                          {os.descricao_problema}
                        </td>
                        <td className="px-4 py-3 text-[var(--color-text-muted)] hidden sm:table-cell">
                          {os.mecanico_nome}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={STATUS_BADGE[os.status] ?? "default"}>
                            {STATUS_LABEL[os.status] ?? os.status}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
