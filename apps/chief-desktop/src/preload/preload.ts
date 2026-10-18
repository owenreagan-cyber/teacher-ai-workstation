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
  history: (sessionId) => electron.ipcRenderer.invoke("chief:history", String(sessionId)),
  brief: () => electron.ipcRenderer.invoke("chief:brief"),
  status: () => electron.ipcRenderer.invoke("chief:status"),
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
