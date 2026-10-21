// Window layout rules for the full Chief window: rail pages, chat modes, the rail breakpoint, and
// keyboard shortcuts. Pure (no DOM, no Electron) so tests run it directly.

export const RAIL_BREAKPOINT_PX = 1100; // below this the rail shows icons only
export const FOCUS_COLUMN_PX = 780;

export type Page = "today" | "chat" | "agents" | "mac" | "files" | "settings";
// ⌘1 … ⌘5, in rail order. Files is shown as "later" and stays disabled.
export const RAIL_PAGES: { page: Page; label: string; enabled: boolean }[] = [
  { page: "today", label: "Today", enabled: true },
  { page: "chat", label: "Chat", enabled: true },
  { page: "agents", label: "Agents & builds", enabled: true },
  { page: "mac", label: "Mac", enabled: true },
  { page: "files", label: "Files", enabled: false },
];

export type ChatMode = "split" | "focus" | "hide";
export const CHAT_MODES: ChatMode[] = ["split", "focus", "hide"];
export const CHAT_MODE_KEY = "chief.chatMode";
export const LAST_OPEN_MODE_KEY = "chief.lastOpenChatMode";

type Store = Pick<Storage, "getItem" | "setItem">;
const isMode = (v: unknown): v is ChatMode => CHAT_MODES.includes(v as ChatMode);

function read(store: Store | null, key: string): string | null {
  try {
    return store?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

/** The remembered chat mode (split when nothing valid is stored). */
export function loadChatMode(store: Store | null): ChatMode {
  const v = read(store, CHAT_MODE_KEY);
  return isMode(v) ? v : "split";
}

export function saveChatMode(store: Store | null, mode: ChatMode): void {
  try {
    store?.setItem(CHAT_MODE_KEY, mode);
    if (mode !== "hide") store?.setItem(LAST_OPEN_MODE_KEY, mode);
  } catch {
    // A lost preference is harmless.
  }
}

/** ⌘\: hide the chat, or bring it back the way it was before it was hidden. */
export function toggleHide(store: Store | null, current: ChatMode): ChatMode {
  if (current !== "hide") return "hide";
  const last = read(store, LAST_OPEN_MODE_KEY);
  return isMode(last) && last !== "hide" ? last : "split";
}

/** Icons only below the breakpoint, and always in Focus. */
export function railCollapsed(widthPx: number, mode: ChatMode): boolean {
  return widthPx < RAIL_BREAKPOINT_PX || mode === "focus";
}

export type Shortcut =
  | { kind: "page"; page: Page }
  | { kind: "toggle-hide" }
  | { kind: "focus-input" }
  | { kind: "hide-window" }
  | null;

/** The app shortcut for a key press, or null. ⌘1–⌘5 rail pages (Files does nothing yet), ⌘\ toggles
 * Hide, ⌘K focuses the chat input, Esc hides the window. */
export function shortcutFor(e: { key: string; metaKey: boolean; ctrlKey: boolean; altKey: boolean; shiftKey: boolean }): Shortcut {
  if (e.key === "Escape" && !e.metaKey && !e.ctrlKey && !e.altKey) return { kind: "hide-window" };
  if (!e.metaKey || e.ctrlKey || e.altKey) return null;
  if (e.key === "\\") return { kind: "toggle-hide" };
  if (e.key.toLowerCase() === "k" && !e.shiftKey) return { kind: "focus-input" };
  const n = Number(e.key);
  if (Number.isInteger(n) && n >= 1 && n <= RAIL_PAGES.length) {
    const entry = RAIL_PAGES[n - 1];
    return entry.enabled ? { kind: "page", page: entry.page } : null;
  }
  return null;
}

export const STARTERS = ["Summarize today", "Diagnose my Mac", "What needs me?"] as const;
