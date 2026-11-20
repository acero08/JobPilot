import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const tokenFile = resolve(process.cwd(), env.VITE_TOKEN_FILE || "../backend/data/api-token");
  // Read on every request so the dev server works even if it starts before the
  // backend has created the token.
  const readToken = () => {
    try { return readFileSync(tokenFile, "utf8").trim(); } catch { return ""; }
  };
  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_DEV_PORT || 5173),
      proxy: {
        "/api": {
          target: env.VITE_API_URL || "http://127.0.0.1:8000",
          configure: (proxy) => {
            proxy.on("proxyReq", (req) => req.setHeader("X-JobPilot-Token", readToken()));
          },
        },
      },
    },
  };
});
