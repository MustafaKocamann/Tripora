import path from "node:path";

import { defineConfig } from "@playwright/test";

process.env.UV_CACHE_DIR ??= ".uv-cache";
process.env.UNDERCOVER_STUB_AGENT = "1";
process.env.UNDERCOVER_DB_PATH = path.resolve(
  "backend",
  `undercover-e2e-${String(process.pid)}.db`,
);

export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  workers: 1,
  use: { baseURL: "http://localhost:5173" },
  webServer: [
    {
      command: "uv run -m uvicorn backend.main:app --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: false,
    },
    {
      command:
        "npx vite --config vite.config.ts --configLoader runner --port 5173 --strictPort",
      url: "http://localhost:5173",
      reuseExistingServer: false,
    },
  ],
});
