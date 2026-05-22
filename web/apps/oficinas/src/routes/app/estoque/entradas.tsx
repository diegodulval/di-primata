import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Skeleton } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, createFileRoute, useNavigate } from "@tanstack/react-router";
import { type ChangeEvent, useRef, useState } from "react";

export const Route = createFileRoute("/app/estoque/entradas")({
  component: EntradasPage,
});

interface RascunhoResumo {
  id: string;
  numero_nf: string | null;
  chave_nfe: string | null;
  data_emissao: string | null;
  valor_total: string | null;
  status: string;
  criado_em: string;
  pendentes: number;
}

const STATUS_LABEL: Record<string, string> = {
  PENDENTE: "Pendente",
  CONFIRMADA: "Confirmada",
  CANCELADA: "Cancelada",
};

function EntradasPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: rascunhos, isLoading } = useQuery({
    queryKey: ["rascunhos"],
    queryFn: () => api.get<RascunhoResumo[]>("/entradas/rascunhos"),
  });

  const importar = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<RascunhoResumo>("/entradas/xml", form);
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["rascunhos"] });
      void navigate({
        to: "/app/estoque/nfe-revisao/$rascunhoId",
        params: { rascunhoId: data.id },
      });
    },
    onError: (err: Error) => {
      setError(
        err instanceof ApiError && err.status === 409
          ? "Esta NF-e já foi importada anteriormente."
          : err.message
      );
    },
  });

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setError(null);
      importar.mutate(file);
    }
  }

  const pendentes = rascunhos?.filter((r) => r.status === "PENDENTE") ?? [];
  const anteriores = rascunhos?.filter((r) => r.status !== "PENDENTE") ?? [];

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center gap-3">
        <Link
          to="/app/estoque"
          className="text-sm text-[--color-text-muted] hover:text-[--color-text-primary]"
        >
          ← Estoque
        </Link>
      </div>

      <h1 className="text-2xl font-bold text-[--color-text-primary]">Importar NF-e</h1>

      <Card>
        <CardHeader>
          <CardTitle>Selecionar arquivo XML</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <input
              ref={fileRef}
              type="file"
              accept=".xml"
              onChange={handleFileChange}
              className="hidden"
            />
            <Button
              type="button"
              variant="outline"
              onClick={() => fileRef.current?.click()}
              disabled={importar.isPending}
            >
              {importar.isPending ? "Processando..." : "Selecionar XML"}
            </Button>
            {fileName && <span className="text-sm text-[--color-text-secondary]">{fileName}</span>}
          </div>
          {error && <p className="mt-3 text-sm text-[--color-error]">{error}</p>}
          <p className="mt-3 text-xs text-[--color-text-muted]">
            O arquivo será analisado e os itens vinculados automaticamente quando possível. Itens
            sem correspondência precisarão de revisão manual antes da confirmação.
          </p>
        </CardContent>
      </Card>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-14 w-full" />
          ))}
        </div>
      ) : (
        <>
          {pendentes.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-sm font-medium text-[--color-text-primary]">
                Aguardando revisão
              </h2>
              {pendentes.map((r) => (
                <RascunhoRow key={r.id} rascunho={r} />
              ))}
            </section>
          )}

          {anteriores.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-sm font-medium text-[--color-text-muted]">Anteriores</h2>
              {anteriores.map((r) => (
                <RascunhoRow key={r.id} rascunho={r} />
              ))}
            </section>
          )}

          {rascunhos?.length === 0 && (
            <p className="text-sm text-[--color-text-muted] text-center py-4">
              Nenhuma importação registrada.
            </p>
          )}
        </>
      )}
    </div>
  );
}

function RascunhoRow({ rascunho }: { rascunho: RascunhoResumo }) {
  const badgeVariant =
    rascunho.status === "CONFIRMADA"
      ? "success"
      : rascunho.status === "CANCELADA"
        ? "secondary"
        : "warning";

  return (
    <Link
      to="/app/estoque/nfe-revisao/$rascunhoId"
      params={{ rascunhoId: rascunho.id }}
      className="block"
    >
      <Card className="hover:bg-[--color-background] transition-colors cursor-pointer">
        <CardContent className="py-3 px-4 flex items-center justify-between gap-4">
          <div className="flex items-center gap-4 min-w-0">
            <div className="min-w-0">
              <p className="text-sm font-medium text-[--color-text-primary] truncate">
                NF-e {rascunho.numero_nf ?? "s/n"}
                {rascunho.data_emissao && (
                  <span className="ml-2 text-[--color-text-muted] font-normal">
                    {rascunho.data_emissao}
                  </span>
                )}
              </p>
              {rascunho.chave_nfe && (
                <p className="text-xs font-mono text-[--color-text-muted] truncate">
                  {rascunho.chave_nfe}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            {rascunho.status === "PENDENTE" && rascunho.pendentes > 0 && (
              <span className="text-xs text-[--color-warning]">
                {rascunho.pendentes} pendente{rascunho.pendentes !== 1 ? "s" : ""}
              </span>
            )}
            {rascunho.valor_total && (
              <span className="text-sm text-[--color-text-secondary]">
                R${" "}
                {Number.parseFloat(rascunho.valor_total).toLocaleString("pt-BR", {
                  minimumFractionDigits: 2,
                })}
              </span>
            )}
            <Badge variant={badgeVariant}>{STATUS_LABEL[rascunho.status] ?? rascunho.status}</Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
