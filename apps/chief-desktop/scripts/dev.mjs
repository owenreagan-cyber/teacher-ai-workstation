// `npm run dev`: compile main + preload (`npm run build:main`), start the Vite dev server on
// http://localhost:5173, and launch Electron pointed at it. Quitting Chief (⌘Q or the menu bar
// icon) stops the dev server. Owen runs this; automated checks never do.
//
// main + preload are compiled through the package script, not by resolving a path inside the
// typescript package: TypeScript 7 no longer exports "typescript/bin/tsc"
// (ERR_PACKAGE_PATH_NOT_EXPORTED). scripts/static-checks.mjs keeps it that way.
import { execFileSync, spawn } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { createServer } from "vite";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(import.meta.url);

// Under `npm run`, npm_execpath is npm's own CLI script; otherwise fall back to npm on PATH.
const npmCli = process.env.npm_execpath;
const [npmCmd, npmArgs] = npmCli ? [process.execPath, [npmCli]] : ["npm", []];
execFileSync(npmCmd, [...npmArgs, "run", "build:main"], { cwd: root, stdio: "inherit" });

const server = await createServer({ configFile: path.join(root, "vite.config.mts") });
await server.listen();
const url = `http://localhost:${server.config.server.port}`;

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
