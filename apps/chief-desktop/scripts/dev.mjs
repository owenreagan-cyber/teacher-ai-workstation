// `npm run dev`: start the Vite dev server on http://localhost:5173, compile main + preload, and
// launch Electron pointed at it. Quitting Chief (⌘Q or the menu bar icon) stops the dev server.
// Owen runs this; automated checks never do.
import { execFileSync, spawn } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);

const server = await createServer({ configFile: path.join(root, "vite.config.mts") });
await server.listen();
const url = `http://localhost:${server.config.server.port}`;

execFileSync(process.execPath, [require.resolve("typescript/bin/tsc"), "-p", "tsconfig.main.json"], { cwd: root, stdio: "inherit" });
execFileSync(process.execPath, [require.resolve("typescript/bin/tsc"), "-p", "tsconfig.preload.json"], { cwd: root, stdio: "inherit" });

const electronBinary = require("electron"); // path to the Electron binary (downloaded on first use)
const child = spawn(electronBinary, ["."], {
  cwd: root,
  stdio: "inherit",
  env: { ...process.env, CHIEF_DEV_URL: url },
});

const shutdown = async (code) => {
  await server.close();
  process.exit(code ?? 0);
};
child.on("exit", (code) => void shutdown(code));
process.on("SIGINT", () => child.kill("SIGTERM"));
process.on("SIGTERM", () => child.kill("SIGTERM"));
