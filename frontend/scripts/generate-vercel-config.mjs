/**
 * Gera vercel.json com proxy das rotas da API para o backend real.
 * VITE_API_URL (ou VITE_BACKEND_URL) deve apontar para o host do FastAPI, não para o domínio da Vercel.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function backendOrigin() {
  const explicit = (process.env.VITE_BACKEND_URL || "").trim();
  if (explicit) return explicit.replace(/\/$/, "");

  const api = (process.env.VITE_API_URL || "").trim();
  if (!api) return null;

  const origin = api.replace(/\/api\/v1\/?$/i, "").replace(/\/$/, "");
  if (!origin || /localhost|127\.0\.0\.1/i.test(origin)) return null;
  if (/vercel\.app/i.test(origin)) {
    console.warn(
      "[vercel] VITE_API_URL aponta para o frontend (.vercel.app). " +
        "Defina VITE_BACKEND_URL (ou API_PUBLIC_URL no backend) com a URL real do FastAPI."
    );
    return null;
  }
  return origin;
}

const backend = backendOrigin();
const apiPrefixes = ["/api", "/content", "/auth", "/users"];
const rewrites = [];

if (backend) {
  for (const prefix of apiPrefixes) {
    rewrites.push({
      source: `${prefix}/:path*`,
      destination: `${backend}${prefix}/:path*`,
    });
  }
  rewrites.push({
    source: "/health",
    destination: `${backend}/health`,
  });
  console.log(`[vercel] Proxy API → ${backend}`);
} else {
  console.warn(
    "[vercel] Sem proxy de API (apenas SPA). Rotas /api e /content no domínio da Vercel retornarão 404."
  );
}

rewrites.push({ source: "/(.*)", destination: "/index.html" });

const vercelConfig = { rewrites };
writeFileSync(join(root, "vercel.json"), JSON.stringify(vercelConfig, null, 2) + "\n");
