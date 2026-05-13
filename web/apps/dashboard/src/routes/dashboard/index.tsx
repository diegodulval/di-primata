import { Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/dashboard/")({
  component: DashboardHome,
});

type Stats = {
  usuarios_ativos: number;
  usuarios_portal: number;
  sessoes_wpp: number;
  mensagens_hoje: number;
};

function useStats() {
  return useQuery<Stats>({
    queryKey: ["bff", "stats"],
    queryFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const res = await fetch("/api/bff/stats", {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) throw new Error("Erro ao carregar estatísticas");
      return res.json();
    },
    refetchInterval: 30_000,
  });
}

function DashboardHome() {
  const { data: stats } = useStats();

  const KPI_ITEMS = [
    {
      title: "Usuários Ativos",
      value: stats?.usuarios_ativos,
      desc: "usuários cadastrados e ativos",
    },
    {
      title: "Acesso ao Portal",
      value: stats?.usuarios_portal,
      desc: "produtores com acesso habilitado",
    },
    {
      title: "Sessões WhatsApp",
      value: stats?.sessoes_wpp,
      desc: "sessões de agente abertas",
    },
    {
      title: "Mensagens Hoje",
      value: stats?.mensagens_hoje,
      desc: "registros via WhatsApp no dia",
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Visão Geral</h1>
        <p className="text-[--color-text-muted] text-sm mt-1">
          Painel operacional da plataforma
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {KPI_ITEMS.map((kpi) => (
          <KpiCard key={kpi.title} title={kpi.title} value={kpi.value} desc={kpi.desc} />
        ))}
      </div>
    </div>
  );
}

function KpiCard({
  title,
  value,
  desc,
}: {
  title: string;
  value: number | undefined;
  desc: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-[--color-text-muted]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold text-[--color-text-primary]">
          {value ?? <span className="text-[--color-border]">—</span>}
        </div>
        <p className="text-xs text-[--color-text-muted] mt-1">{desc}</p>
      </CardContent>
    </Card>
  );
}
