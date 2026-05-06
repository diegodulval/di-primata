import { createContext, useContext, useEffect, type ReactNode } from "react";

export type Palette = "floresta" | "oliva" | "terra" | "brisa";

export interface TenantConfig {
  tenantId: string;
  palette: Palette;
  brandName: string;
  logoUrl?: string;
  modules: Array<"transparency" | "integration" | "intelligence" | "security">;
  publicPortal?: {
    showMap: boolean;
    certificationBadge: boolean;
  };
}

const DEFAULT_CONFIG: TenantConfig = {
  tenantId: "default",
  palette: "oliva",
  brandName: "Di Mata",
  modules: ["transparency", "integration", "intelligence", "security"],
};

const ThemeContext = createContext<TenantConfig>(DEFAULT_CONFIG);

interface ThemeProviderProps {
  config?: Partial<TenantConfig>;
  children: ReactNode;
}

export function ThemeProvider({ config, children }: ThemeProviderProps) {
  const resolved: TenantConfig = { ...DEFAULT_CONFIG, ...config };

  useEffect(() => {
    const root = document.documentElement;
    const palettes: Palette[] = ["floresta", "oliva", "terra", "brisa"];
    palettes.forEach((p) => root.classList.remove(`theme-${p}`));
    root.classList.add(`theme-${resolved.palette}`);
  }, [resolved.palette]);

  return <ThemeContext.Provider value={resolved}>{children}</ThemeContext.Provider>;
}

export function useTenant(): TenantConfig {
  return useContext(ThemeContext);
}
