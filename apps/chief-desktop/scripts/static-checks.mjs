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
  [/\bfetch\s*\(/, "fetch("], [/\bnet\.request\b/, "net.request"],
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
const ALLOWED = ["ask", "history", "openLink", "brief", "status", "stop", "resume", "setPin", "setProtection", "hide", "onEvent"];
const bridgeBody = preload.match(/const bridge: PreloadBridge = \{([\s\S]*?)\n\};/)?.[1] ?? "";
const keys = [...bridgeBody.matchAll(/^ {2}(\w+):/gm)].map((m) => m[1]);
check("preload exposes exactly the allowed functions", JSON.stringify(keys) === JSON.stringify(ALLOWED), keys.join(","));
check("preload exposes only window.chief", (preload.match(/exposeInMainWorld\(/g) ?? []).length === 1 && preload.includes('exposeInMainWorld("chief", bridge)'));
const invokes = [...preload.matchAll(/ipcRenderer\.invoke\(([^,)]+)/g)].map((m) => m[1]);
check("every invoke uses a literal chief: channel", invokes.length === 10 && invokes.every((c) => /^"chief:[a-z-]+"$/.test(c)), invokes.join(","));
check("preload never sends or exposes ipcRenderer", !/ipcRenderer\.(send|sendSync|postMessage)\b/.test(preload) && !/exposeInMainWorld\([^)]*ipcRenderer/.test(preload));

// 6b. cos warm: main process only, on launch and when shown after more than 90 minutes hidden.
check("buildArgs has warm", /case "warm":\s*return \["warm", "--json"\];/.test(read("src/main/args.ts")));
check("main warms the model on launch", /registerIpc\(\);\s*warmModel\(\);/.test(mainTs));
check("main re-warms after more than 90 minutes hidden",
  mainTs.includes("REWARM_AFTER_HIDDEN_MS = 90 * 60 * 1000") && /Date\.now\(\) - hiddenSince > REWARM_AFTER_HIDDEN_MS\) warmModel\(\)/.test(mainTs));
check("warm runs through cos warm --json", /this\.json\("warm"\)/.test(cosTs));
check("warm has no preload bridge or IPC channel", !/warm/i.test(preload) && !/chief:warm/.test(mainTs));

// 6c. Home card: rendered only inside the content-protected window. Its content never reaches the
// tray, a window or document title, a notification, or the dock; the main process never reads it.
const rendererFiles = walk("src/renderer", [".ts", ".tsx", ".html"]);
const mainFiles = [...walk("src/main", [".ts"]), ...walk("src/preload", [".ts"])];
for (const file of mainFiles) {
  const text = read(file);
  check("main never sets a tray title or tooltip", !/\.(setTitle|setToolTip)\s*\(/.test(text), file);
  check("main shows no notifications", !/\bNotification\b/.test(text), file);
  check("main never touches the dock badge or menu", !/\bapp\.dock\b|setBadge/.test(text), file);
  // cos.ts only validates the card and returns it to the renderer; the window and tray code never see it.
  if (file !== path.join("src", "main", "cos.ts")) {
    check("main never reads home card content", !/\bcard\b|homeCard|HomeCard/.test(text.replace(/^\s*\/\/.*$/gm, "")), file);
  }
}
for (const file of rendererFiles) {
  const text = read(file);
  check("renderer never sets document.title", !/document\.title/.test(text), file);
  check("renderer shows no notifications", !/\bNotification\b/.test(text), file);
}
check("index.html title is the fixed name", /<title>Chief<\/title>/.test(html));
check("home card renders only from App", rendererFiles.filter((f) => /<HomeCardView\b/.test(read(f))).join() === path.join("src", "renderer", "App.tsx"));
check("cos runner validates the card", /card: toHomeCard\(o\.card\)/.test(cosTs));

// 6d. Start at login: set only by the main process (never from preload, renderer, or an IPC call),
// only in the packaged app; a login launch starts hidden and still warms the model.
const loginSetters = [...mainFiles, ...rendererFiles].filter((f) => /setLoginItemSettings/.test(read(f)));
check("login item is set only in src/main/main.ts", loginSetters.join() === path.join("src", "main", "main.ts"), loginSetters.join());
check("login item calls are main-process only (no IPC channel)", !/chief:[a-z-]*login/i.test(mainTs) && !/login/i.test(preload));
check("login item is only set by the packaged app", /function setStartAtLogin[\s\S]*?if \(!app\.isPackaged\) return;[\s\S]*?setLoginItemSettings\(\{ openAtLogin: enabled \}\)/.test(mainTs));
check("first run turns start at login on", /if \(prefs\.startAtLogin === null\) setStartAtLogin\(true\)/.test(mainTs));
check("a login launch starts hidden", /createWindow\(!openedAtLogin\(\)\)/.test(mainTs) && /wasOpenedAtLogin/.test(mainTs));
check("tray has a Start at login toggle", /label: app\.isPackaged \? "Start at login"/.test(mainTs) && /click: \(\) => setStartAtLogin\(!startAtLoginChecked\(\)\)/.test(mainTs));
check("the model still warms on every launch", /createTray\(\);\s*registerHotkey\(\);\s*registerIpc\(\);\s*warmModel\(\);/.test(mainTs));

// 6e. Search answers carry "Search by Brave" in the window.
check("search answers show Brave attribution", /searchAttribution\(turn\)/.test(read("src/renderer/App.tsx")));

// 6e2. Auto web search: a tray checkbox in the main process that runs `cos auto-search on|off`.
// No preload bridge or IPC channel can change it; cos writes its own config.json.
check("buildArgs has auto-search", /case "auto-search":[\s\S]*?\["auto-search", params\.enabled === true \? "on" : "off", "--json"\]/.test(read("src/main/args.ts")));
check("tray has an Auto web search toggle", /label: "Auto web search",\s*type: "checkbox"/.test(mainTs) && /click: \(\) => void toggleAutoSearch\(\)/.test(mainTs));
check("auto search has no preload bridge or IPC channel", !/auto.?search/i.test(preload) && !/chief:[a-z-]*auto/i.test(mainTs));

// 6g. Links (P1a.5): URLs stay in the main process. The renderer gets link ids; the only call that
// opens anything is openLink(linkId), looked up in the main process's resource table, https only.
const opens = mainFiles.flatMap((f) => [...read(f).matchAll(/shell\.openExternal\(([^)]*)\)/g)].map((m) => `${f}:${m[1]}`));
check("shell.openExternal is called exactly once, with a URL from the resource table",
  opens.length === 1 && opens[0] === `${path.join("src", "main", "main.ts")}:url` &&
  /handle\("chief:open-link", \(linkId\) => openLink\(resources, linkId, \(url\) => shell\.openExternal\(url\)\)\)/.test(mainTs),
  opens.join(","));
const resourcesTs = read("src/main/resources.ts");
check("openLink looks the id up and re-checks https", /const url = table\.get\(linkId\)/.test(resourcesTs) && /return url === undefined \? null : httpsUrl\(url\)/.test(resourcesTs));
check("preload openLink passes only a string id", /openLink: \(linkId\) => electron\.ipcRenderer\.invoke\("chief:open-link", String\(linkId\)\)/.test(preload));
check("renderer-bound text has URLs removed", /answer: stripUrls\(answer\)/.test(cosTs) && /notices: notices\.map\(stripUrls\)/.test(cosTs) && /blocks: toBlocks\(o\.blocks\)/.test(cosTs));
check("resources go to the main process sink, not the renderer", /this\.onResources\(resourcesOf\(v\)\)/.test(cosTs) && !/resources/.test(read("src/shared/types.ts").replace(/^\s*\/\/.*$/gm, "")));
for (const file of rendererFiles) {
  check("renderer source holds no URL", !/https?:\/\//.test(read(file).replace(/xmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, "")), file);
}
const blocksTsx = read("src/renderer/Blocks.tsx");
check("suggestion buttons send only their message text", /onClick=\{\(\) => \{ const m = suggestionMessage\(b, j\); if \(m !== null\) onSend\(m\); \}\}/.test(blocksTsx));
check("suggestions use the same ask path as typing", /onSend=\{\(m\) => void send\(m\)\}/.test(read("src/renderer/App.tsx")) &&
  /const question = \(message \?\? input\)\.trim\(\);/.test(read("src/renderer/App.tsx")));
check("rain animation is off for reduced motion", /prefers-reduced-motion: reduce[\s\S]*chief-rain[\s\S]*animation: none/.test(read("src/renderer/styles.css")));

// 6f. Packaging: every build checks that the startup modules are packaged (and inside app.asar
// after `npm run package`), so a missing file fails the build instead of the installed app.
const pkgJson = JSON.parse(read("package.json"));
check("build runs the packaging check", /&& node scripts\/check-package\.mjs$/.test(pkgJson.scripts.build));
check("package checks app.asar", /electron-builder [^&]*&& node scripts\/check-package\.mjs --asar$/.test(pkgJson.scripts.package));

// 7. Dev script: no package-internal paths (TypeScript 7 stopped exporting typescript/bin/tsc,
// which broke `npm run dev` with ERR_PACKAGE_PATH_NOT_EXPORTED). Compile through build:main.
const devMjs = read("scripts/dev.mjs");
const devCode = devMjs.split("\n").filter((l) => !l.trimStart().startsWith("//")).join("\n");
const specifiers = [
  ...devCode.matchAll(/\b(?:require(?:\.resolve)?|import)\s*\(\s*["']([^"']+)["']/g),
  ...devCode.matchAll(/\bfrom\s+["']([^"']+)["']/g),
].map((m) => m[1]);
const internal = specifiers.filter((s) => {
  if (s.startsWith("node:") || s.startsWith(".") || s.startsWith("/")) return false;
  const parts = s.split("/");
  return parts.length > (s.startsWith("@") ? 2 : 1); // "pkg/sub" or "@scope/pkg/sub"
});
check("dev.mjs resolves no package-internal paths", internal.length === 0, internal.join(","));
check("dev.mjs never names typescript/bin", !/typescript\/bin/.test(devCode));
check("dev.mjs compiles main + preload via npm run build:main", /"run",\s*"build:main"/.test(devCode));

if (failures.length) {
  console.error(`static checks: ${failures.length} failed, ${passed} passed`);
  for (const f of failures) console.error(`  FAIL ${f}`);
  process.exit(1);
}
console.log(`static checks: ${passed} passed, 0 failed`);
