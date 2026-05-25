import { ApiError, api } from "@/lib/api";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle } from "@di-mata/ui";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

const TIPOS = ["carro", "moto", "caminhao", "van"] as const;

const MARCAS_VEICULOS = [
  "Acura","ADLY","Agrale","Alfa Romeo","AM General","Amazonas","Aprilia","Asia Motors",
  "Aston Martin","Atala","Audi","AVELLOZ","Baby","Bajaj","Bee","Benelli","Bepobus",
  "Beta","Bimota","BMW","Brandy","Brava","BRM","BRP","Buell","Bueno","Bugre","Bull",
  "byCristo","BYD","CAB Motors","Cagiva","Caloi","Caoa Chery","Case","CBT Jipe","Chana",
  "Changan","Chery","Chevrolet","Chrysler","Ciccobus","Citroën","Cross Lander","D2D",
  "DAF","Daelim","Daewoo","Dafra","Daihatsu","Dayang","Dayun","Derbi","DFSK","Dodge",
  "Ducati","Effa","Effa-JMC","Emme","Engesa","Envemo","Ferrari","Fever","Fiat",
  "Fibravan","Ford","Foton","Fox","Fusco Motosegura","Fyber","FYM","Garinni","Gas Gas",
  "Geely","GM - Chevrolet","GMC","Great Wall","Green","Gurgel","GWM","Hafei","Haobao",
  "Haojue","Harley-Davidson","Hartford","Hero","Hitech Electric","Honda","Husaberg",
  "Husqvarna","Hyundai","Indian","Iros","Isuzu","Iveco","Jac","Jaguar","Jeep",
  "Jiapeng Volcano","Jinei","John Deere","Johnnypag","Jonny","JPX","Kahena","Kasinski",
  "Kawasaki","Kia Motors","KTM","Kymco","L Aquila","Lada","Lamborghini","Land Rover",
  "Landum","Lavrale","Lerivo","Lexus","Lifan","Lobini","Lon-V","Lotus",
  "Magrão Triciclos","Mahindra","Malaguti","MAN","Marcopolo","Mascarello","Maserati",
  "Massey Ferguson","Matra","Maxibus","Mazda","Mclaren","Mercedes-Benz","Mercury","MG",
  "MINI","Mitsubishi","Miura","Miza","Moto Guzzi","Motocar","Motorino","MRX",
  "MV Augusta","MVK","Navistar","Neobus","New Holland","NIU","Nissan","Orca","Pegassi",
  "Peugeot","Piaggio","Plymouth","Polaris","Pontiac","Porsche","Puma-Alfa","RAM",
  "Regal Raptor","Rely","Renault","Riguete","Rolls-Royce","Rover","Royal Enfield","Saab",
  "Saab-Scania","Sanyang","Saturn","Scania","Seat","Seres","Shacman","Shineray",
  "Siamoto","Sinotruk","smart","Ssangyong","Subaru","Sundown","Super Soco","Suzuki",
  "TAC","Targos","Tiger","Toyota","Traxx","Triumph","Troller","Valtra",
  "Ventane Motors","Vento","Volkswagen","Voltz","Volvo","Wake","Walk","Walkbus","Watts",
  "Wuayang","Yamaha","Zontes",
].sort((a, b) => a.localeCompare(b, "pt-BR"));

function VeiculosPage() {
  const queryClient = useQueryClient();
  const [placa, setPlaca] = useState("");
  const [query, setQuery] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // form de cadastro
  const [fPlaca, setFPlaca] = useState("");
  const [fMarca, setFMarca] = useState("");
  const [fModelo, setFModelo] = useState("");
  const [fAnoFab, setFAnoFab] = useState("");
  const [fAnoMod, setFAnoMod] = useState("");
  const [fCor, setFCor] = useState("");
  const [fTipo, setFTipo] = useState<(typeof TIPOS)[number] | "">("");
  const [formErro, setFormErro] = useState<string | null>(null);

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

  const salvar = useMutation({
    mutationFn: () =>
      api.post<VeiculoDetalhe>("/veiculos", {
        placa: fPlaca.trim().toUpperCase(),
        marca: fMarca || null,
        modelo: fModelo || null,
        ano_fab: fAnoFab ? Number(fAnoFab) : null,
        ano_mod: fAnoMod ? Number(fAnoMod) : null,
        cor: fCor || null,
        tipo: fTipo || null,
      }),
    onSuccess: (v) => {
      void queryClient.invalidateQueries({ queryKey: ["veiculo"] });
      setQuery(v.placa);
      setShowForm(false);
      setFormErro(null);
    },
    onError: (err: Error) => setFormErro(err.message),
  });

  function abrirFormNovo() {
    setFPlaca(placa);
    setFMarca("");
    setFModelo("");
    setFAnoFab("");
    setFAnoMod("");
    setFCor("");
    setFTipo("");
    setFormErro(null);
    setShowForm(true);
  }

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[--color-text-primary]">Veículos</h1>
        <Button size="sm" onClick={abrirFormNovo}>
          + Cadastrar veículo
        </Button>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
        <input
          value={placa}
          onChange={(e) => setPlaca(e.target.value.toUpperCase())}
          placeholder="ABC1234 ou ABC1D23"
          maxLength={8}
          className="rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm font-mono uppercase w-48 focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
        />
        <Button type="submit" size="sm" disabled={isLoading}>
          {isLoading ? "Buscando..." : "Buscar"}
        </Button>
      </form>

      {notFound && (
        <div className="flex items-center gap-3">
          <p className="text-sm text-[--color-text-muted]">
            Placa <strong>{query}</strong> não encontrada.
          </p>
          <Button size="sm" variant="outline" onClick={abrirFormNovo}>
            Cadastrar esta placa
          </Button>
        </div>
      )}

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>Cadastrar veículo</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1">
                <label
                  htmlFor="v-placa"
                  className="text-sm font-medium text-[--color-text-primary]"
                >
                  Placa *
                </label>
                <input
                  id="v-placa"
                  required
                  value={fPlaca}
                  onChange={(e) => setFPlaca(e.target.value.toUpperCase())}
                  maxLength={8}
                  placeholder="ABC1234"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm font-mono uppercase focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
              </div>
              <div className="space-y-1">
                <label htmlFor="v-tipo" className="text-sm font-medium text-[--color-text-primary]">
                  Tipo
                </label>
                <select
                  id="v-tipo"
                  value={fTipo}
                  onChange={(e) => setFTipo(e.target.value as (typeof TIPOS)[number] | "")}
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                >
                  <option value="">Selecione...</option>
                  {TIPOS.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1">
                <label
                  htmlFor="v-marca"
                  className="text-sm font-medium text-[--color-text-primary]"
                >
                  Marca
                </label>
                <input
                  id="v-marca"
                  list="marcas-lista"
                  value={fMarca}
                  onChange={(e) => setFMarca(e.target.value)}
                  placeholder="Toyota"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
                <datalist id="marcas-lista">
                  {MARCAS_VEICULOS.map((m) => (
                    <option key={m} value={m} />
                  ))}
                </datalist>
              </div>
              <div className="space-y-1">
                <label
                  htmlFor="v-modelo"
                  className="text-sm font-medium text-[--color-text-primary]"
                >
                  Modelo
                </label>
                <input
                  id="v-modelo"
                  value={fModelo}
                  onChange={(e) => setFModelo(e.target.value)}
                  placeholder="Corolla"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
              </div>
              <div className="space-y-1">
                <label
                  htmlFor="v-ano-fab"
                  className="text-sm font-medium text-[--color-text-primary]"
                >
                  Ano fab.
                </label>
                <input
                  id="v-ano-fab"
                  type="number"
                  value={fAnoFab}
                  onChange={(e) => setFAnoFab(e.target.value)}
                  placeholder="2020"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
              </div>
              <div className="space-y-1">
                <label
                  htmlFor="v-ano-mod"
                  className="text-sm font-medium text-[--color-text-primary]"
                >
                  Ano mod.
                </label>
                <input
                  id="v-ano-mod"
                  type="number"
                  value={fAnoMod}
                  onChange={(e) => setFAnoMod(e.target.value)}
                  placeholder="2021"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
              </div>
              <div className="space-y-1">
                <label htmlFor="v-cor" className="text-sm font-medium text-[--color-text-primary]">
                  Cor
                </label>
                <input
                  id="v-cor"
                  value={fCor}
                  onChange={(e) => setFCor(e.target.value)}
                  placeholder="Prata"
                  className="w-full rounded-md border border-[--color-border] bg-[var(--color-surface)] px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[--color-primary]"
                />
              </div>
            </div>
            {formErro && <p className="text-sm text-[--color-error] mt-2">{formErro}</p>}
            <div className="flex gap-2 justify-end mt-4">
              <Button type="button" size="sm" variant="outline" onClick={() => setShowForm(false)}>
                Cancelar
              </Button>
              <Button
                type="button"
                size="sm"
                disabled={!fPlaca || salvar.isPending}
                onClick={() => salvar.mutate()}
              >
                {salvar.isPending ? "Salvando..." : "Salvar"}
              </Button>
            </div>
          </CardContent>
        </Card>
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
