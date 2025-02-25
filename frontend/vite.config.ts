import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");

  let host = "0.0.0.0";
  let port = 5173;

  if (env.VITE_HOST) {
    host = env.VITE_HOST;
  }

  if (env.VITE_PORT) {
    port = parseInt(env.VITE_PORT, 10);
  }

  console.log(`Server will start on host: ${host} and port: ${port}`);

  return {
    plugins: [react()],
    server: {
      host,
      port,
      strictPort: true,
    },
    build: {
      outDir: "dist",
      assetsDir: "assets",
    },
  };
});
