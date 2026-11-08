// The only bridge between the sandboxed renderer and the main process: window.chief, with one
// named function per allowed request. No generic invoke/send passthrough.
// Written as a script (no import/export) so the sandboxed preload loader can run tsc's output.

type PreloadBridge = import("../shared/types").ChiefBridge;
type PreloadEvent = import("../shared/types").ShellEvent;
type PreloadState = import("../shared/types").WindowState;

const electron = require("electron") as typeof import("electron");

const listeners = new Set<(event: PreloadEvent) => void>();
let lastWindowState: PreloadState | null = null;

electron.ipcRenderer.on("chief:event", (_e, event: PreloadEvent) => {
  if (event.kind === "window-state") lastWindowState = event.state;
  for (const listener of listeners) listener(event);
});

const bridge: PreloadBridge = {
  ask: (question, sessionId) => electron.ipcRenderer.invoke("chief:ask", String(question), String(sessionId)),
  cancelAsk: () => electron.ipcRenderer.invoke("chief:cancel-ask"),
  history: (sessionId) => electron.ipcRenderer.invoke("chief:history", String(sessionId)),
  openLink: (linkId) => electron.ipcRenderer.invoke("chief:open-link", String(linkId)),
  brief: () => electron.ipcRenderer.invoke("chief:brief"),
  home: (cached) => electron.ipcRenderer.invoke("chief:home", cached === true),
  configGet: () => electron.ipcRenderer.invoke("chief:config-get"),
  configSet: (key, value) => electron.ipcRenderer.invoke("chief:config-set", String(key), value),
  status: () => electron.ipcRenderer.invoke("chief:status"),
  cosdConnection: () => electron.ipcRenderer.invoke("chief:cosd-connection"),
  cosdReconnect: () => electron.ipcRenderer.invoke("chief:cosd-reconnect"),
  listTasks: (state) => electron.ipcRenderer.invoke("chief:tasks-list", state ?? ""),
  getTask: (taskId) => electron.ipcRenderer.invoke("chief:task-get", String(taskId)),
  createTask: (title, kind, idempotencyKey) =>
    electron.ipcRenderer.invoke("chief:task-create", String(title), String(kind), String(idempotencyKey)),
  cancelTask: (taskId) => electron.ipcRenderer.invoke("chief:task-cancel", String(taskId)),
  retryTask: (taskId) => electron.ipcRenderer.invoke("chief:task-retry", String(taskId)),
  taskHistory: (taskId) => electron.ipcRenderer.invoke("chief:task-history", String(taskId)),
  queueSnapshot: () => electron.ipcRenderer.invoke("chief:queue"),
  stop: () => electron.ipcRenderer.invoke("chief:stop"),
  resume: () => electron.ipcRenderer.invoke("chief:resume"),
  setPin: (pinned) => electron.ipcRenderer.invoke("chief:set-pin", pinned === true),
  setProtection: (enabled) => electron.ipcRenderer.invoke("chief:set-protection", enabled === true),
  hide: () => electron.ipcRenderer.invoke("chief:hide"),
  onEvent: (listener) => {
    const wrapped = (event: PreloadEvent) => listener(event);
    listeners.add(wrapped);
    // Replay the current window state to a late subscriber (it is sent on page load).
    if (lastWindowState) wrapped({ kind: "window-state", state: lastWindowState });
    return () => {
      listeners.delete(wrapped);
    };
  },
};

electron.contextBridge.exposeInMainWorld("chief", bridge);
