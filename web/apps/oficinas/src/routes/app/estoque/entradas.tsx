import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useMutation } from "@tanstack/react-query";
import { Link, createFileRoute } from "@tanstack/react-router";
import { type ChangeEvent, useRef, useState } from "react";

export const Route = createFileRoute("/app/estoque/entradas")({
  component: EntradasPage,
});

interface ItemEntrada {
  id: string;
  codigo_fornecedor: string | null;
  quantidade: string;
  preco_unitario: string;
  icms: string;
  ipi: string;
}

interface EntradaNfe {
  id: string;
  chave_nfe: string | null;
  numero_nf: string | null;
  data_emissao: string | null;
  valor_total: string | null;
  status: string;
  itens: ItemEntrada[];
}

function EntradasPage() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [result, setResult] = useState<EntradaNfe | null>(null);
  const [error, setError] = useState<string | null>(null);

  const importar = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("arquivo", file);
      return api.postForm<EntradaNfe>("/entradas/xml", form);
    },
    onSuccess: (data) => {
      setResult(data);
      setError(null);
    },
    onError: (err: Error) => {
      setResult(null);
      if (err instanceof ApiError && err.status === 409) {
        setError("Esta NF-e já foi importada anteriormente.");
      } else {
        setError(err.message);
      }
    },
  });

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setFileName(file.name);
      setResult(null);
      setError(null);
      importar.mutate(file);
    }
  }

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
          <CardTitle>Arquivo XML</CardTitle>
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
        </CardContent>
      </Card>

      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <CardTitle>NF-e importada</CardTitle>
              <Badge variant="success">{result.status}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <dl className="grid grid-cols-2 sm:grid-cols-3 gap-x-8 gap-y-3 text-sm">
              <div>
                <dt className="text-[--color-text-muted]">Número</dt>
                <dd className="text-[--color-text-primary]">{result.numero_nf ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[--color-text-muted]">Emissão</dt>
                <dd className="text-[--color-text-primary]">{result.data_emissao ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-[--color-text-muted]">Total</dt>
                <dd className="text-[--color-text-primary] font-medium">
                  {result.valor_total
                    ? `R$ ${Number.parseFloat(result.valor_total).toLocaleString("pt-BR", {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2,
                      })}`
                    : "—"}
                </dd>
              </div>
              <div className="col-span-2 sm:col-span-3">
                <dt className="text-[--color-text-muted]">Chave</dt>
                <dd className="font-mono text-xs text-[--color-text-secondary] break-all">
                  {result.chave_nfe ?? "—"}
                </dd>
              </div>
            </dl>

            {result.itens.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-[--color-text-primary] mb-2">
                  Itens ({result.itens.length})
                </h3>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[--color-border] text-left text-[--color-text-muted]">
                      <th className="pb-2 pr-4 font-medium">Cód. fornecedor</th>
                      <th className="pb-2 pr-4 font-medium text-right">Qtd</th>
                      <th className="pb-2 pr-4 font-medium text-right">Preço unit.</th>
                      <th className="pb-2 pr-4 font-medium text-right hidden sm:table-cell">
                        ICMS %
                      </th>
                      <th className="pb-2 font-medium text-right hidden sm:table-cell">IPI %</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[--color-border]">
                    {result.itens.map((item) => (
                      <tr key={item.id}>
                        <td className="py-2 pr-4 font-mono text-xs text-[--color-text-secondary]">
                          {item.codigo_fornecedor ?? "—"}
                        </td>
                        <td className="py-2 pr-4 text-right text-[--color-text-primary]">
                          {Number.parseFloat(item.quantidade).toFixed(3)}
                        </td>
                        <td className="py-2 pr-4 text-right text-[--color-text-primary]">
                          {Number.parseFloat(item.preco_unitario).toLocaleString("pt-BR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="py-2 pr-4 text-right text-[--color-text-secondary] hidden sm:table-cell">
                          {item.icms}
                        </td>
                        <td className="py-2 text-right text-[--color-text-secondary] hidden sm:table-cell">
                          {item.ipi}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
