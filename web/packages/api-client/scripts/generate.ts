import { writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "../src/generated/schema.ts");

const apiUrl = process.env["API_URL"] ?? "http://localhost:8000/openapi.json";
const healthUrl = apiUrl.replace("/openapi.json", "/health");

// Verifica se a API está no ar antes de tentar gerar
try {
  const res = await fetch(healthUrl);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
} catch {
  console.error(`
❌  API indisponível em: ${healthUrl}

    Suba a API antes de gerar o schema:

        make run

    Em seguida rode novamente:

        make web-generate
        # ou: cd web && pnpm generate:api
`);
  process.exit(1);
}

console.log(`📥  Buscando schema em: ${apiUrl}`);
const ast = await openapiTS(new URL(apiUrl));
const content = astToString(ast);

writeFileSync(OUT, content, "utf-8");
console.log(`✅  Schema gerado em:\n    ${OUT}`);
