import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/")({
  component: HomePage,
});

interface ClienteList {
  total: number;
}

function KpiCard({
  title,
  value,
  loading,
}: {
  title: string;
  value: number | string;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[--color-text-muted]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-16" />
        ) : (
          <p className="text-3xl font-bold text-[--color-text-primary]">{value}</p>
        )}
      </CardContent>
    </Card>
  );
}

function HomePage() {
  const clientes = useQuery({
    queryKey: ["clientes-count"],
    queryFn: () => api.get<ClienteList>("/clientes"),
  });

  const produtos = useQuery({
    queryKey: ["produtos-count"],
    queryFn: () => api.get<unknown[]>("/produtos"),
  });

  const fornecedores = useQuery({
    queryKey: ["fornecedores-count"],
    queryFn: () => api.get<unknown[]>("/fornecedores"),
  });

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold text-[--color-text-primary] mb-2">Início</h1>
      <p className="text-sm text-[--color-text-muted] mb-6">Visão geral da oficina</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <KpiCard
          title="Clientes cadastrados"
          value={clientes.data?.total ?? 0}
          loading={clientes.isLoading}
        />
        <KpiCard
          title="Produtos em estoque"
          value={Array.isArray(produtos.data) ? produtos.data.length : 0}
          loading={produtos.isLoading}
        />
        <KpiCard
          title="Fornecedores"
          value={Array.isArray(fornecedores.data) ? fornecedores.data.length : 0}
          loading={fornecedores.isLoading}
        />
      </div>
    </div>
  );
}
