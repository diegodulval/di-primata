import { api } from "@/lib/api";
import { Badge, Button, Card, CardContent, Skeleton } from "@di-mata/ui";
import { useQuery } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";

export const Route = createFileRoute("/app/vendas/")({
  component: VendasPage,
});

interface Venda {
  id: string;
  numero_venda: string;
  cliente_id: string | null;
  total: string;
  status: string;
  criado_em: string;
}

function VendasPage() {
  const { data: vendas, isLoading } = useQuery({
    queryKey: ["vendas"],
    queryFn: () => api.get<Venda[]>("/vendas"),
  });

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Vendas</h1>
        <Link to="/app/vendas/nova">
          <Button size="sm">+ Nova venda</Button>
        </Link>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : !vendas?.length ? (
            <p className="text-sm text-[--color-text-muted] py-8 text-center">
              Nenhuma venda registrada.
            </p>
          ) : (
            vendas.map((v) => (
              <div
                key={v.id}
                className="px-4 py-3 border-b border-[--color-border] last:border-0 flex items-center justify-between gap-4"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-[--color-text-primary]">
                    {v.numero_venda}
                  </p>
                  <p className="text-xs text-[--color-text-muted]">
                    {new Date(v.criado_em).toLocaleString("pt-BR", {
                      day: "2-digit",
                      month: "2-digit",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge variant="success">{v.status}</Badge>
                  <span className="text-sm font-mono font-semibold text-[--color-text-primary]">
                    {Number(v.total).toLocaleString("pt-BR", {
                      style: "currency",
                      currency: "BRL",
                    })}
                  </span>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
