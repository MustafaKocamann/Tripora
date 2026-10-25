import { defineConfig } from "@playwright/test";

process.env.UV_CACHE_DIR ??= ".uv-cache";

export default defineConfig({
  testDir: "e2e",
  outputDir: "e2e/test-results",
  reporter: "list",
  use: { baseURL: "http://localhost:5173" },
  webServer: [
    {
      command: "uv run -m uvicorn backend.main:app --port 8000",
      url: "http://127.0.0.1:8000/api/health",
      reuseExistingServer: true,
    },
    {
      command:
        "npx vite --config vite.config.ts --configLoader runner --port 5173 --strictPort",
      url: "http://localhost:5173",
      reuseExistingServer: true,
    },
  ],
});
