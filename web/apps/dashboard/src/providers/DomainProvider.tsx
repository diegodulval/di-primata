import type { DomainSchema } from "@di-mata/shared";
import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, type ReactNode } from "react";

const DEFAULT_SCHEMA: DomainSchema = {
  domain: "rural",
  labels: {
    account: { singular: "Propriedade", plural: "Propriedades" },
    unit: { singular: "Talhão", plural: "Talhões" },
    cycle: { singular: "Safra", plural: "Safras" },
    event: { singular: "Atividade", plural: "Atividades" },
    user: { singular: "Produtor", plural: "Produtores" },
    product: { singular: "Cultura", plural: "Culturas" },
  },
  unit_types: [{ value: "TALHAO", label: "Talhão" }],
  event_types: [{ value: "adubacao", label: "Adubação" }],
  setor_options: [],
  features: [],
};

const DomainContext = createContext<DomainSchema>(DEFAULT_SCHEMA);

export function DomainProvider({ children }: { children: ReactNode }) {
  const { data } = useQuery<DomainSchema>({
    queryKey: ["bff", "schema"],
    queryFn: async () => {
      const token = sessionStorage.getItem("access_token");
      const res = await fetch("/api/bff/schema", {
        headers: { Authorization: token ? `Bearer ${token}` : "" },
      });
      if (!res.ok) return DEFAULT_SCHEMA;
      return res.json();
    },
    staleTime: Infinity,
  });

  return <DomainContext.Provider value={data ?? DEFAULT_SCHEMA}>{children}</DomainContext.Provider>;
}

export function useDomain(): DomainSchema {
  return useContext(DomainContext);
}
