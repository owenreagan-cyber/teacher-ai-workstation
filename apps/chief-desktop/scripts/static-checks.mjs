// Static security checks for the desktop shell (run by `npm test`). Exits 1 on any failure.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (rel) => fs.readFileSync(path.join(root, rel), "utf-8");
const walk = (rel, exts) =>
  fs.readdirSync(path.join(root, rel), { withFileTypes: true }).flatMap((e) => {
    const child = path.join(rel, e.name);
    if (e.isDirectory()) return walk(child, exts);
    return exts.includes(path.extname(e.name)) ? [child] : [];
  });

const failures = [];
let passed = 0;
function check(name, ok, detail = "") {
  if (ok) passed++;
  else failures.push(`${name}${detail ? `: ${detail}` : ""}`);
}

// 1. Renderer: no network, no Node, no dynamic code.
const RENDERER_FORBIDDEN = [
  "fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "require(", "child_process",
  "eval(", "new Function", "import(", "<webview", "ipcRenderer",
];
for (const file of walk("src/renderer", [".ts", ".tsx", ".html", ".css"])) {
  const text = read(file);
  for (const token of RENDERER_FORBIDDEN) check(`renderer has no ${token}`, !text.includes(token), file);
}

// 2. Main: execFile only, no shell, no network modules.
const MAIN_FORBIDDEN = [
  [/\bexec\s*\(/, "exec("], [/\bexecSync\b/, "execSync"], [/\bspawn(Sync)?\s*\(/, "spawn("], [/\bfork\s*\(/, "fork("],
  [/\bshell\s*:/, "shell option"], [/["']node:(https?|net|tls|dgram|http2)["']/, "network module"],
  [/\bfetch\s*\(/, "fetch("], [/\bnet\.request\b/, "net.request"], [/\bshell\.openExternal\b/, "shell.openExternal"],
  [/webviewTag\s*:\s*true/, "webviewTag: true"], [/nodeIntegration\s*:\s*true/, "nodeIntegration: true"],
];
for (const file of [...walk("src/main", [".ts"]), ...walk("src/preload", [".ts"])]) {
  const text = read(file);
  for (const [re, label] of MAIN_FORBIDDEN) check(`main/preload has no ${label}`, !re.test(text), file);
}
const cosTs = read("src/main/cos.ts");
check("cos runner uses execFile", /\bexecFile\s*\(/.test(cosTs));
check("execFile gets the minimal env", /env:\s*minimalEnv\(\)/.test(cosTs));
check("execFile gets a timeout", /\btimeout\b/.test(cosTs));

// 3. BrowserWindow security flags.
const mainTs = read("src/main/main.ts");
for (const flag of ["contextIsolation: true", "nodeIntegration: false", "sandbox: true", "webSecurity: true"]) {
  check(`BrowserWindow has ${flag}`, mainTs.includes(flag));
}
check("devTools only when unpackaged", mainTs.includes("devTools: !app.isPackaged"));
check("content protection on at creation", mainTs.includes("win.setContentProtection(true)"));
check("window title is Chief", mainTs.includes('const TITLE = "Chief"') && mainTs.includes("page-title-updated"));

// 4. CSP: identical in index.html and the session header, with connect-src 'none'.
const html = read("src/renderer/index.html");
const securityTs = read("src/main/security.ts");
const metaCsp = html.match(/http-equiv="Content-Security-Policy"\s+content="([^"]+)"/)?.[1] ?? "";
const headerCsp = (securityTs.match(/export const CSP =([\s\S]*?);\n/)?.[1] ?? "")
  .split("\n").map((l) => l.trim().replace(/^\+?\s*"/, "").replace(/"\s*\+?$/, "")).join("");
check("index.html CSP has connect-src 'none'", metaCsp.includes("connect-src 'none'"));
check("header CSP has connect-src 'none'", headerCsp.includes("connect-src 'none'"));
check("index.html and header CSP are identical", metaCsp === headerCsp, `${metaCsp} !== ${headerCsp}`);
check("CSP header set on session responses", securityTs.includes("onHeadersReceived") && securityTs.includes('"Content-Security-Policy"'));

// 5. Navigation, windows, webviews, permissions, network.
check("will-navigate is blocked", /"will-navigate",\s*\(event\)\s*=>\s*event\.preventDefault\(\)/.test(securityTs));
check("will-attach-webview is blocked", /"will-attach-webview",\s*\(event\)\s*=>\s*event\.preventDefault\(\)/.test(securityTs));
check("new windows are denied", /setWindowOpenHandler\(\(\)\s*=>\s*\(\{\s*action:\s*"deny"\s*\}\)\)/.test(securityTs));
check("permission requests are denied", /setPermissionRequestHandler\([^)]*\)\s*=>\s*callback\(false\)\)/.test(securityTs));
check("permission checks are denied", securityTs.includes("setPermissionCheckHandler(() => false)"));
check("non-local requests are cancelled", securityTs.includes("onBeforeRequest"));
check("dev server only when unpackaged and on localhost", securityTs.includes("!app.isPackaged") && securityTs.includes("http:\\/\\/localhost:"));

// 6. Preload: exactly the allowed bridge, fixed channels only.
const preload = read("src/preload/preload.ts");
const ALLOWED = ["ask", "history", "brief", "status", "stop", "resume", "setPin", "setProtection", "hide", "onEvent"];
const bridgeBody = preload.match(/const bridge: PreloadBridge = \{([\s\S]*?)\n\};/)?.[1] ?? "";
const keys = [...bridgeBody.matchAll(/^ {2}(\w+):/gm)].map((m) => m[1]);
check("preload exposes exactly the allowed functions", JSON.stringify(keys) === JSON.stringify(ALLOWED), keys.join(","));
check("preload exposes only window.chief", (preload.match(/exposeInMainWorld\(/g) ?? []).length === 1 && preload.includes('exposeInMainWorld("chief", bridge)'));
const invokes = [...preload.matchAll(/ipcRenderer\.invoke\(([^,)]+)/g)].map((m) => m[1]);
check("every invoke uses a literal chief: channel", invokes.length === 9 && invokes.every((c) => /^"chief:[a-z-]+"$/.test(c)), invokes.join(","));
check("preload never sends or exposes ipcRenderer", !/ipcRenderer\.(send|sendSync|postMessage)\b/.test(preload) && !/exposeInMainWorld\([^)]*ipcRenderer/.test(preload));

if (failures.length) {
  console.error(`static checks: ${failures.length} failed, ${passed} passed`);
  for (const f of failures) console.error(`  FAIL ${f}`);
  process.exit(1);
}
console.log(`static checks: ${passed} passed, 0 failed`);
