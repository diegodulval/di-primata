import { createFileRoute } from "@tanstack/react-router";
import { Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useTenant } from "@di-mata/theme";

export const Route = createFileRoute("/dashboard/")({
  component: DashboardHome,
});

function DashboardHome() {
  const tenant = useTenant();

  return (
    <div className="p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-[--color-text-primary]">
          Bem-vindo ao {tenant.brandName}
        </h1>
        <p className="text-[--color-text-muted] text-sm mt-1">
          Painel de rastreabilidade da cadeia produtiva
        </p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <KpiCard title="Ciclos Abertos" />
        <KpiCard title="Lotes Gerados" />
        <KpiCard title="Conformidade de Protocolo" />
      </div>
    </div>
  );
}

function KpiCard({ title }: { title: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-[--color-text-muted]">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-8 w-24" />
      </CardContent>
    </Card>
  );
}
