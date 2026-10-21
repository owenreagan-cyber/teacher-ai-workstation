import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import type { NeedAction } from "../shared/home";
import { type ChatMode, loadChatMode, type Page, railCollapsed, saveChatMode, shortcutFor, toggleHide } from "../shared/layout";
import type { ErrorKind, StatusResult, Turn, WindowState } from "../shared/types";
import { type Card, type CardBody, ChatPanel, copyText, ModeControl } from "./Chat";
import { errorMessage, statusDot } from "./messages";
import { Rail } from "./Rail";
import { SettingsPage } from "./Settings";
import { AgentsPage, type HomeState, MacPage, TodayPage } from "./Today";

const SESSION = "default";
const STATUS_POLL_MS = 30_000;
const HOME_POLL_MS = 30_000; // cos refreshes only the sections that are due
const CLOCK_TICK_MS = 30_000; // greeting, date, and freshness labels follow the clock
const MAX_INPUT_LINES = 4;

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function App() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [cards, setCards] = useState<Card[]>([]);
  const [pending, setPending] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [asking, setAsking] = useState(false);
  const [briefing, setBriefing] = useState(false);
  const [status, setStatus] = useState<StatusResult | null>(null);
  const [windowState, setWindowState] = useState<WindowState | null>(null);
  const [home, setHome] = useState<HomeState>({ state: "loading" });
  const [page, setPage] = useState<Page>("today");
  const [mode, setModeState] = useState<ChatMode>(() => loadChatMode(storage()));
  const [width, setWidth] = useState(() => window.innerWidth);
  const [now, setNow] = useState(() => new Date());

  const feedRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const stickToBottom = useRef(true);
  const nextCardId = useRef(1);
  const turnCount = useRef(0);
  const homeBusy = useRef(false);
  turnCount.current = turns.length;

  // The chat mode is remembered across restarts (a per-window preference, not cos state).
  const setMode = useCallback((next: ChatMode) => {
    saveChatMode(storage(), next);
    setModeState(next);
  }, []);

  const addCard = useCallback((card: CardBody) => {
    const full: Card = { ...card, id: nextCardId.current++, afterTurns: turnCount.current };
    setCards((prev) => [...prev, full]);
  }, []);

  const addError = useCallback(
    (kind: ErrorKind, detail: string) => addCard({ kind: "error", text: errorMessage(kind, detail) }),
    [addCard],
  );

  const refreshStatus = useCallback(async () => {
    setStatus(await window.chief.status());
  }, []);

  const loadHistory = useCallback(async () => {
    const res = await window.chief.history(SESSION);
    if (res.ok) setTurns(res.turns);
    else addError(res.error_kind, res.error);
    return res.ok;
  }, [addError]);

  // Cache first: paint what cos last saw at once, then let cos refresh what is due.
  const loadHome = useCallback(async (cached: boolean) => {
    if (homeBusy.current) return;
    homeBusy.current = true;
    try {
      const res = await window.chief.home(cached);
      if (res.ok) setHome({ state: "ready", snap: res });
      else setHome((prev) => (prev.state === "ready" ? prev : { state: "error", text: errorMessage(res.error_kind, res.error) }));
    } finally {
      homeBusy.current = false;
    }
  }, []);

  const runBrief = useCallback(async () => {
    setBriefing(true);
    try {
      const res = await window.chief.brief();
      if (res.ok) addCard({ kind: "brief", lines: res.lines });
      else addError(res.error_kind, res.error);
      setModeState((m) => {
        if (m !== "hide") return m;
        saveChatMode(storage(), "split");
        return "split"; // the brief shows in the chat
      });
    } finally {
      setBriefing(false);
      void refreshStatus();
    }
  }, [addCard, addError, refreshStatus]);

  useEffect(() => {
    void loadHome(true).then(() => loadHome(false));
    const poll = setInterval(() => {
      if (document.visibilityState === "visible") void loadHome(false);
    }, HOME_POLL_MS);
    const tick = setInterval(() => setNow(new Date()), CLOCK_TICK_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        setNow(new Date());
        void loadHome(false);
      }
    };
    const onResize = () => setWidth(window.innerWidth);
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener("resize", onResize);
    return () => {
      clearInterval(poll);
      clearInterval(tick);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener("resize", onResize);
    };
  }, [loadHome]);

  const goTo = useCallback(
    (next: Page) => {
      if (next === "files") return; // later
      if (next === "chat") {
        setMode("focus");
        return;
      }
      setPage(next);
      if (mode === "focus") setMode("split");
    },
    [mode, setMode],
  );

  const focusInput = useCallback(() => {
    if (mode === "hide") setMode("split");
    setTimeout(() => inputRef.current?.focus(), 0);
  }, [mode, setMode]);

  // Launch: history, status, tray notices, and the keyboard.
  useEffect(() => {
    void loadHistory();
    void refreshStatus();
    const timer = setInterval(() => void refreshStatus(), STATUS_POLL_MS);
    const off = window.chief.onEvent((event) => {
      if (event.kind === "window-state") setWindowState(event.state);
      else if (event.kind === "status-changed") void refreshStatus();
      else if (event.kind === "brief-requested") void runBrief();
    });
    return () => {
      clearInterval(timer);
      off();
    };
  }, [loadHistory, refreshStatus, runBrief]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const s = shortcutFor(e);
      if (s === null) return;
      e.preventDefault();
      if (s.kind === "hide-window") void window.chief.hide();
      else if (s.kind === "toggle-hide") setMode(toggleHide(storage(), mode));
      else if (s.kind === "focus-input") focusInput();
      else goTo(s.page);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mode, setMode, focusInput, goTo]);

  // Auto-scroll to the newest item unless Owen has scrolled up.
  useLayoutEffect(() => {
    const feed = feedRef.current;
    if (feed && stickToBottom.current) feed.scrollTop = feed.scrollHeight;
  }, [turns, cards, pending, mode]);

  const onScroll = () => {
    const feed = feedRef.current;
    if (feed) stickToBottom.current = feed.scrollHeight - feed.scrollTop - feed.clientHeight < 48;
  };

  // Grow the input up to four lines.
  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    const line = parseFloat(getComputedStyle(el).lineHeight) || 20;
    const pad = el.offsetHeight - el.clientHeight + 12;
    el.style.height = `${Math.min(el.scrollHeight, line * MAX_INPUT_LINES + pad)}px`;
  }, [input, mode]);

  // Typed input, or a starter or suggestion button's message (text only, through the same ask path).
  const send = async (message?: string) => {
    const question = (message ?? input).trim();
    if (!question || asking) return;
    stickToBottom.current = true;
    if (mode === "hide") setMode("split");
    setAsking(true);
    setPending(question);
    setInput("");
    try {
      const res = await window.chief.ask(question, SESSION);
      if (res.ok) {
        // The feed shows the session as cos recorded it.
        if (!(await loadHistory())) {
          setTurns((prev) => [...prev, { ...res, question }]);
        }
      } else {
        addError(res.error_kind, res.error);
        if (message === undefined) setInput(question); // give typed text back so it can be retried
      }
    } finally {
      setPending(null);
      setAsking(false);
      void refreshStatus();
      inputRef.current?.focus();
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      void send();
    }
  };

  const toggleKillSwitch = async () => {
    if (!status?.ok) return;
    const res = await (status.kill_switch ? window.chief.resume() : window.chief.stop());
    if (!res.ok) addError(res.error_kind, res.error);
    await refreshStatus();
    void loadHome(false);
  };

  // A need's action: a link opens by id in the main process, a page switches here, a command is
  // copied so Owen can run it. Nothing here runs a command.
  const onAction = (action: NeedAction) => {
    if (action.type === "open_link") void window.chief.openLink(action.link_id);
    else if (action.type === "page") goTo(action.page as Page);
    else copyText(action.command);
  };

  const dot = statusDot(status, asking || briefing);
  const stopped = status?.ok ? status.kill_switch : null;
  const collapsed = railCollapsed(width, mode);
  const activePage: Page = mode === "focus" ? "chat" : page;

  const chat = (
    <ChatPanel
      turns={turns}
      cards={cards}
      pending={pending}
      input={input}
      asking={asking}
      focus={mode === "focus"}
      inputRef={inputRef}
      feedRef={feedRef}
      onScroll={onScroll}
      onInput={setInput}
      onKeyDown={onKeyDown}
      onSend={(m) => void send(m)}
    />
  );

  let content: React.ReactNode;
  if (mode === "focus") content = chat;
  else if (page === "mac") content = <MacPage home={home} now={now} />;
  else if (page === "agents") content = <AgentsPage home={home} now={now} />;
  else if (page === "settings") content = <SettingsPage windowState={windowState} onWindowState={setWindowState} />;
  else {
    content = (
      <TodayPage
        home={home}
        now={now}
        briefing={briefing}
        onBrief={() => void runBrief()}
        onAction={onAction}
        onRetry={() => {
          setHome({ state: "loading" });
          void loadHome(false);
        }}
      />
    );
  }

  return (
    <div className="flex h-full bg-bg text-ink">
      <Rail collapsed={collapsed} active={activePage} dot={dot} stopped={stopped} onPage={goTo} onKillSwitch={() => void toggleKillSwitch()} />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="drag flex h-[44px] shrink-0 items-center justify-end gap-2 border-b border-line px-4">
          <ModeControl mode={mode} onMode={setMode} />
        </header>
        <div className="flex min-h-0 flex-1">
          <main className="min-w-0 flex-1 overflow-y-auto">{content}</main>
          {mode === "split" && <aside className="w-[400px] shrink-0 border-l border-line bg-bg">{chat}</aside>}
        </div>
      </div>
    </div>
  );
}
