// Chief desktop shell, main process. A client of cos: it displays what cos returns and asks cos to
// act. Policy, routing, the fast path, model calls, audit, the kill switch, and data handling all
// stay in the Python core.
import path from "node:path";

import {
  app,
  BrowserWindow,
  globalShortcut,
  shell,
  ipcMain,
  type IpcMainInvokeEvent,
  Menu,
  type MenuItemConstructorOptions,
  screen,
  Tray,
} from "electron";

import { addMacSample, type MacSample } from "../shared/home.js";
import type { HomeResult, ShellEvent, StatusResult, WindowState } from "../shared/types.js";
import {
  loadDesktopConfig,
  loadPrefs,
  loadWindowState,
  MAX_SIZE,
  MIN_SIZE,
  type Prefs,
  type SavedWindow,
  savePrefs,
  saveWindowState,
} from "./config.js";
import { CosRunner } from "./cos.js";
import { openLink, ResourceTable } from "./resources.js";
import { APP_URL, devServerUrl, lockDownContents, lockDownSession, registerAppScheme, serveRenderer } from "./security.js";
import { trayTemplateImage } from "./trayIcon.js";

const TITLE = "Chief";
const REWARM_AFTER_HIDDEN_MS = 90 * 60 * 1000; // re-warm the model when shown after this long hidden

let win: BrowserWindow | null = null;
let tray: Tray | null = null;
let quitting = false;
let hotkeyNotice: string | null = null;
let lastKillSwitch: boolean | null = null; // from the latest cos status, for the tray label only
let lastAutoSearch: boolean | null = null; // from the latest cos status, for the tray checkbox only
let saved: SavedWindow;
let windowState: WindowState = { pinned: false, protected: true, startAtLogin: null, hotkey: "" };
let hiddenSince: number | null = null;
let warming = false;
let prefs: Prefs = { startAtLogin: null };
let macHistory: MacSample[] = [];

const config = loadDesktopConfig();
const resources = new ResourceTable(); // link id -> URL; never sent to the renderer
const cos = new CosRunner(config.cosPath, config.error, (list) => resources.add(list));
const devUrl = devServerUrl();
const stateFile = () => path.join(app.getPath("userData"), "window-state.json");
const prefsFile = () => path.join(app.getPath("userData"), "prefs.json");

registerAppScheme();
app.on("web-contents-created", (_event, contents) => lockDownContents(contents));

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => showWindow());
  app.whenReady().then(start);
}

function start(): void {
  lockDownSession(devUrl);
  serveRenderer(path.join(__dirname, "..", "..", "dist", "renderer"));
  Menu.setApplicationMenu(appMenu());
  saved = loadWindowState(stateFile());
  prefs = loadPrefs(prefsFile());
  if (prefs.startAtLogin === null) setStartAtLogin(true); // first run: on by default
  createWindow(!openedAtLogin());
  createTray();
  registerHotkey();
  registerIpc();
  warmModel(); // in the background: the first question should not wait for a cold model load
}

// Main process only (no preload bridge): `cos warm --json` loads the model with its keep_alive.
// Fire and forget; at most one at a time. cos refuses it while the kill switch is set.
function warmModel(): void {
  if (warming) return;
  warming = true;
  void cos.warm().finally(() => {
    warming = false;
  });
}

// ----------------------------------------------------------------------------- login item

// Main process only: no preload bridge or IPC channel can change it. Only the packaged app registers
// itself, so `npm run dev` never adds the bare Electron binary as a login item.
// Electron 44 dropped `openAsHidden` (macOS 13+ ignores it under SMAppService), so a login launch
// is detected with wasOpenedAtLogin and the window simply stays hidden; the model still warms.
function setStartAtLogin(enabled: boolean): void {
  if (!app.isPackaged) return;
  app.setLoginItemSettings({ openAtLogin: enabled });
  prefs = { ...prefs, startAtLogin: enabled };
  savePrefs(prefsFile(), prefs);
  windowState = { ...windowState, startAtLogin: enabled };
  sendEvent({ kind: "window-state", state: windowState });
}

function startAtLoginChecked(): boolean {
  // macOS is the truth (Owen may remove it in System Settings); the remembered choice otherwise.
  return app.isPackaged ? app.getLoginItemSettings().openAtLogin : prefs.startAtLogin === true;
}

function openedAtLogin(): boolean {
  return app.isPackaged && app.getLoginItemSettings().wasOpenedAtLogin;
}

// ----------------------------------------------------------------------------- window

function onScreen(x: number | undefined, y: number | undefined, width: number): boolean {
  if (x === undefined || y === undefined) return false;
  return screen.getAllDisplays().some(({ workArea: a }) =>
    x >= a.x - width / 2 && y >= a.y && x + width / 2 <= a.x + a.width && y + 40 <= a.y + a.height);
}

function createWindow(showWhenReady: boolean): void {
  const placed = onScreen(saved.x, saved.y, saved.width);
  win = new BrowserWindow({
    title: TITLE,
    width: saved.width,
    height: saved.height,
    ...(placed ? { x: saved.x, y: saved.y } : {}),
    minWidth: MIN_SIZE.width,
    minHeight: MIN_SIZE.height,
    maxWidth: MAX_SIZE.width,
    maxHeight: MAX_SIZE.height,
    titleBarStyle: "hiddenInset",
    show: false,
    fullscreenable: false,
    backgroundColor: "#00000000",
    webPreferences: {
      preload: path.join(__dirname, "..", "preload", "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true,
      devTools: !app.isPackaged,
      webviewTag: false,
      spellcheck: false,
    },
  });

  // Every launch starts protected, whatever was remembered.
  windowState = { pinned: saved.pinned, protected: true, startAtLogin: startAtLoginChecked(), hotkey: config.hotkey };
  win.setContentProtection(true);
  if (windowState.pinned) win.setAlwaysOnTop(true, "floating");

  win.on("page-title-updated", (event) => event.preventDefault());
  win.on("close", (event) => {
    if (!quitting) {
      event.preventDefault(); // the red button hides; quit is ⌘Q or the menu bar icon
      win?.hide();
    }
  });
  let saveTimer: NodeJS.Timeout | undefined;
  const scheduleSave = () => {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(rememberWindow, 500);
  };
  win.on("hide", () => {
    hiddenSince = Date.now();
  });
  win.on("show", () => {
    if (hiddenSince !== null && Date.now() - hiddenSince > REWARM_AFTER_HIDDEN_MS) warmModel();
    hiddenSince = null;
    // Owen may change the login item in System Settings; Settings shows what macOS says now.
    windowState = { ...windowState, startAtLogin: startAtLoginChecked() };
    sendEvent({ kind: "window-state", state: windowState });
  });
  win.on("resize", scheduleSave);
  win.on("move", scheduleSave);
  win.webContents.on("did-finish-load", () => sendEvent({ kind: "window-state", state: windowState }));
  // Started at login: stay hidden in the menu bar until the hotkey or the tray opens the window.
  win.once("ready-to-show", () => {
    if (showWhenReady) win?.show();
  });

  void (devUrl ? win.loadURL(devUrl) : win.loadURL(APP_URL));
}

function rememberWindow(): void {
  if (!win || win.isDestroyed()) return;
  const b = win.getBounds();
  saved = { x: b.x, y: b.y, width: b.width, height: b.height, pinned: windowState.pinned, protected: windowState.protected };
  saveWindowState(stateFile(), saved);
}

function showWindow(): void {
  if (!win) return;
  if (win.isMinimized()) win.restore();
  win.show();
  win.focus();
}

function toggleWindow(): void {
  if (!win) return;
  if (win.isVisible() && !win.isMinimized() && win.isFocused()) win.hide();
  else showWindow();
}

function setPin(pinned: boolean): WindowState {
  windowState = { ...windowState, pinned };
  win?.setAlwaysOnTop(pinned, "floating");
  rememberWindow();
  sendEvent({ kind: "window-state", state: windowState });
  return windowState;
}

function setProtection(enabled: boolean): WindowState {
  windowState = { ...windowState, protected: enabled };
  win?.setContentProtection(enabled);
  rememberWindow();
  sendEvent({ kind: "window-state", state: windowState });
  return windowState;
}

// The Today snapshot. Each fresh Mac reading becomes a sample for the trend lines: the last 30
// minutes, kept in this process's memory only (never written to disk).
async function home(cached: boolean): Promise<HomeResult> {
  const res = await cos.home(cached);
  if (!res.ok) return res;
  const at = res.mac.generated_at ? Date.parse(res.mac.generated_at) : NaN;
  if (res.mac.data && Number.isFinite(at)) {
    macHistory = addMacSample(macHistory, { t: at, memory_free_pct: res.mac.data.memory_free_pct, cpu_load_pct: res.mac.data.cpu_load_pct });
  }
  return { ...res, mac_history: macHistory };
}

function sendEvent(event: ShellEvent): void {
  if (win && !win.isDestroyed()) win.webContents.send("chief:event", event);
}

// ----------------------------------------------------------------------------- tray and hotkey

function createTray(): void {
  tray = new Tray(trayTemplateImage()); // no title, no tooltip: nothing from conversations
  const open = async () => {
    await refreshKillSwitch();
    tray?.popUpContextMenu(trayMenu());
  };
  tray.on("click", () => void open());
  tray.on("right-click", () => void open());
}

async function refreshKillSwitch(): Promise<void> {
  const status = await cos.status();
  lastKillSwitch = status.ok ? status.kill_switch : null;
  lastAutoSearch = status.ok ? status.auto_search : null;
}

// Main process only (no preload bridge): cos writes auto_search in its own config.json.
async function toggleAutoSearch(): Promise<void> {
  if (lastAutoSearch === null) return;
  const res = await cos.setAutoSearch(!lastAutoSearch);
  if (res.ok) lastAutoSearch = res.auto_search;
}

function trayMenu(): Menu {
  const items: MenuItemConstructorOptions[] = [];
  if (hotkeyNotice) items.push({ label: hotkeyNotice, enabled: false }, { type: "separator" });
  items.push(
    { label: win?.isVisible() ? "Hide Chief" : "Show Chief", click: () => toggleWindow() },
    {
      label: "Daily Brief",
      click: () => {
        showWindow();
        sendEvent({ kind: "brief-requested" });
      },
    },
    { type: "separator" },
    lastKillSwitch
      ? { label: "Resume Chief", click: () => void control("resume") }
      : { label: "Stop Chief", enabled: lastKillSwitch !== null, click: () => void control("stop") },
    {
      label: "Auto web search",
      type: "checkbox",
      checked: lastAutoSearch === true,
      enabled: lastAutoSearch !== null,
      click: () => void toggleAutoSearch(),
    },
    {
      label: `Screen protection: ${windowState.protected ? "on" : "off"}`,
      type: "checkbox",
      checked: windowState.protected,
      click: () => setProtection(!windowState.protected),
    },
    {
      label: app.isPackaged ? "Start at login" : "Start at login (packaged app only)",
      type: "checkbox",
      checked: startAtLoginChecked(),
      enabled: app.isPackaged,
      click: () => setStartAtLogin(!startAtLoginChecked()),
    },
    { type: "separator" },
    { label: "Quit Chief", click: () => app.quit() },
  );
  return Menu.buildFromTemplate(items);
}

async function control(action: "stop" | "resume"): Promise<void> {
  await (action === "stop" ? cos.stop() : cos.resume());
  sendEvent({ kind: "status-changed" });
}

function registerHotkey(): void {
  let ok = false;
  try {
    ok = globalShortcut.register(config.hotkey, toggleWindow);
  } catch {
    ok = false; // malformed accelerator
  }
  hotkeyNotice = ok ? null : `Hotkey ${config.hotkey} could not be registered`;
}

function appMenu(): Menu {
  return Menu.buildFromTemplate([
    { role: "appMenu" },
    { role: "editMenu" }, // copy / paste / select all in the input
    { role: "windowMenu" },
  ]);
}

app.on("activate", () => showWindow());
app.on("before-quit", () => {
  quitting = true;
  rememberWindow();
});
app.on("will-quit", () => globalShortcut.unregisterAll());
app.on("window-all-closed", () => {
  // Closing hides the window; the app keeps running in the menu bar until Quit.
});

// ----------------------------------------------------------------------------- IPC

function trusted(event: IpcMainInvokeEvent): boolean {
  const url = event.senderFrame?.url ?? "";
  if (!win || event.sender !== win.webContents) return false;
  return url.startsWith(APP_URL.replace("index.html", "")) || (devUrl !== null && url.startsWith(new URL(devUrl).origin + "/"));
}

function handle(channel: string, fn: (...args: unknown[]) => unknown): void {
  ipcMain.handle(channel, (event, ...args) => {
    if (!trusted(event)) throw new Error("untrusted sender");
    return fn(...args);
  });
}

function registerIpc(): void {
  handle("chief:ask", (question, sessionId) => cos.ask(question, sessionId));
  handle("chief:history", (sessionId) => cos.history(sessionId));
  // The only way a link opens: by id, looked up in the main process's table, https only.
  handle("chief:open-link", (linkId) => openLink(resources, linkId, (url) => shell.openExternal(url)));
  handle("chief:brief", () => cos.brief());
  handle("chief:home", (cached) => home(cached === true));
  // Settings: cos validates every write (config schema, settable keys); buildArgs re-checks the key.
  handle("chief:config-get", () => cos.configGet());
  handle("chief:config-set", (key, value) => cos.configSet(key, value));
  handle("chief:status", async () => {
    const status: StatusResult = await cos.status();
    lastKillSwitch = status.ok ? status.kill_switch : null;
    lastAutoSearch = status.ok ? status.auto_search : null;
    return status;
  });
  handle("chief:stop", () => cos.stop());
  handle("chief:resume", () => cos.resume());
  handle("chief:set-pin", (pinned) => setPin(pinned === true));
  handle("chief:set-protection", (enabled) => setProtection(enabled === true));
  handle("chief:hide", () => win?.hide());
}
