import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Renderer only. Main and preload are compiled by tsc (tsconfig.main.json).
export default defineConfig({
  root: "src/renderer",
  base: "./",
  plugins: [tailwindcss()],
  build: {
    outDir: "../../dist/renderer",
    emptyOutDir: true,
    sourcemap: false,
    modulePreload: { polyfill: false }, // the polyfill would need inline script / fetch
  },
  server: {
    host: "localhost",
    port: 5173,
    strictPort: true,
    hmr: false, // the CSP blocks the HMR websocket (connect-src 'none'); reload manually
  },
});
