import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  let host = "0.0.0.0";
  let port = 5173;
  const backendUrl = env.VITE_BACKEND_URL || "http://localhost:8000";

  if (env.VITE_HOST) {
    host = env.VITE_HOST;
  }

  if (env.VITE_PORT) {
    port = parseInt(env.VITE_PORT, 10);
  }

  return {
    plugins: [react()],
    server: {
      host,
      port,
      strictPort: true,
      proxy: {
        // Proxy all /api requests to the backend
        "/api": {
          target: backendUrl,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
    build: {
      outDir: "dist",
      assetsDir: "assets",
    },
  };
});
