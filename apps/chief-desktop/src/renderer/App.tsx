import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";

import type { ErrorKind, StatusResult, Turn, WindowState } from "../shared/types";
import { BriefIcon, ExpandIcon, PinIcon, PlayIcon, ShieldIcon, StopIcon } from "./icons";
import { errorMessage, statusDot } from "./messages";

const SESSION = "default";
const STATUS_POLL_MS = 30_000;
const MAX_INPUT_LINES = 4;

// Display-only cards (Daily Brief, errors). Never saved into the session.
type CardBody = { kind: "brief"; lines: string[] } | { kind: "error"; text: string };
type Card = CardBody & { id: number; afterTurns: number };

const DOT_CLASS = {
  green: "bg-emerald-500",
  amber: "bg-amber-400 animate-pulse",
  red: "bg-red-500",
  gray: "bg-neutral-400",
} as const;

function copyText(text: string): boolean {
  // execCommand needs no clipboard permission (every permission is denied in this app).
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  const ok = document.execCommand("copy");
  area.remove();
  return ok;
}

function HeaderButton(props: { label: string; active?: boolean; disabled?: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      title={props.label}
      aria-label={props.label}
      aria-pressed={props.active}
      disabled={props.disabled}
      onClick={props.onClick}
      className={`no-drag rounded-md p-1.5 transition-colors disabled:opacity-40 ${
        props.active
          ? "text-sky-600 dark:text-sky-400 bg-sky-500/10"
          : "text-neutral-500 hover:bg-neutral-500/10 hover:text-neutral-800 dark:hover:text-neutral-100"
      }`}
    >
      {props.children}
    </button>
  );
}

function AnswerFooter({ turn }: { turn: Pick<Turn, "fast_path" | "model" | "tools_used" | "total_ms"> }) {
  // Rendered only from the turn's JSON as cos returned it.
  const engine = turn.fast_path ? "fast path (no model)" : (turn.model ?? "model not reported");
  const tools = turn.tools_used.length ? turn.tools_used.join(", ") : "none";
  return (
    <div className="mt-1.5 text-[10.5px] leading-4 text-neutral-500">
      {engine} · Tools: {tools} · {turn.total_ms} ms
    </div>
  );
}

function TurnView({ turn }: { turn: Turn }) {
  const [copied, setCopied] = useState(false);
  const onCopy = () => {
    if (copyText(turn.answer)) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };
  return (
    <div className="space-y-2">
      <div className="flex justify-end">
        <div className="selectable max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-sky-600 px-3 py-2 text-[13px] text-white">
          {turn.question}
        </div>
      </div>
      <div className="flex justify-start">
        <div className="max-w-[92%] rounded-2xl rounded-bl-md bg-neutral-200/70 px-3 py-2 text-[13px] dark:bg-neutral-800">
          <div className="selectable whitespace-pre-wrap break-words">{turn.answer}</div>
          {turn.notices.map((n, i) => (
            <div key={i} className="selectable mt-1 text-[12px] text-amber-700 dark:text-amber-400">
              Note: {n}
            </div>
          ))}
          <div className="flex items-end justify-between gap-2">
            <AnswerFooter turn={turn} />
            <button
              type="button"
              onClick={onCopy}
              className="shrink-0 rounded px-1.5 text-[10.5px] text-neutral-500 hover:bg-neutral-500/15 hover:text-neutral-800 dark:hover:text-neutral-100"
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function CardView({ card }: { card: Card }) {
  if (card.kind === "brief") {
    return (
      <div className="selectable rounded-xl border border-neutral-300/70 bg-white/60 px-3 py-2 text-[12px] leading-5 dark:border-neutral-700 dark:bg-neutral-900/60">
        <div className="mb-1 text-[10.5px] font-medium uppercase tracking-wide text-neutral-500">Daily Brief · not saved</div>
        {card.lines.map((line, i) => (
          <div key={i} className={`whitespace-pre-wrap ${i === 0 ? "font-medium" : ""}`}>
            {line}
          </div>
        ))}
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-amber-400/50 bg-amber-50 px-3 py-2 text-[12px] text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
      {card.text}
    </div>
  );
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

  const feedRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const stickToBottom = useRef(true);
  const nextCardId = useRef(1);
  const turnCount = useRef(0);
  turnCount.current = turns.length;

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

  const runBrief = useCallback(async () => {
    setBriefing(true);
    try {
      const res = await window.chief.brief();
      if (res.ok) addCard({ kind: "brief", lines: res.lines });
      else addError(res.error_kind, res.error);
    } finally {
      setBriefing(false);
      void refreshStatus();
    }
  }, [addCard, addError, refreshStatus]);

  // Launch: history, status, and subscribe to tray notices.
  useEffect(() => {
    void loadHistory();
    void refreshStatus();
    const timer = setInterval(() => void refreshStatus(), STATUS_POLL_MS);
    const off = window.chief.onEvent((event) => {
      if (event.kind === "window-state") setWindowState(event.state);
      else if (event.kind === "status-changed") void refreshStatus();
      else if (event.kind === "brief-requested") void runBrief();
    });
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") void window.chief.hide();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      clearInterval(timer);
      off();
      window.removeEventListener("keydown", onKey);
    };
  }, [loadHistory, refreshStatus, runBrief]);

  // Auto-scroll to the newest item unless Owen has scrolled up.
  useLayoutEffect(() => {
    const feed = feedRef.current;
    if (feed && stickToBottom.current) feed.scrollTop = feed.scrollHeight;
  }, [turns, cards, pending]);

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
  }, [input]);

  const send = async () => {
    const question = input.trim();
    if (!question || asking) return;
    stickToBottom.current = true;
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
        setInput(question); // give the question back so it can be retried
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
  };

  const dot = statusDot(status, asking || briefing);
  const stopped = status?.ok ? status.kill_switch : null;
  const isProtected = windowState?.protected ?? true;

  const feed: React.ReactNode[] = [];
  for (let i = 0; i <= turns.length; i++) {
    for (const card of cards.filter((c) => c.afterTurns === i)) feed.push(<CardView key={`c${card.id}`} card={card} />);
    if (i < turns.length) feed.push(<TurnView key={`t${i}-${turns[i].ts}`} turn={turns[i]} />);
  }

  return (
    <div className="flex h-full flex-col bg-neutral-50 text-neutral-900 dark:bg-neutral-900 dark:text-neutral-100">
      <header className="drag flex h-[38px] shrink-0 items-center gap-1 border-b border-neutral-200 pl-[78px] pr-2 dark:border-neutral-800">
        <span className={`h-2 w-2 shrink-0 rounded-full ${DOT_CLASS[dot.color]}`} title={dot.label} aria-label={dot.label} />
        <span className="ml-1 truncate text-[11px] text-neutral-500">{dot.label}</span>
        <div className="flex-1" />
        <HeaderButton
          label={isProtected ? "Screen protection on (hidden from screenshots and sharing)" : "Screen protection off"}
          active={isProtected}
          disabled={windowState === null}
          onClick={() => void window.chief.setProtection(!isProtected).then(setWindowState)}
        >
          <ShieldIcon on={isProtected} />
        </HeaderButton>
        <HeaderButton
          label={windowState?.pinned ? "Unpin (stop floating on top)" : "Pin on top"}
          active={windowState?.pinned ?? false}
          disabled={windowState === null}
          onClick={() => void window.chief.setPin(!windowState?.pinned).then(setWindowState)}
        >
          <PinIcon on={windowState?.pinned ?? false} />
        </HeaderButton>
        <HeaderButton label="Daily Brief" disabled={briefing} onClick={() => void runBrief()}>
          <BriefIcon />
        </HeaderButton>
      </header>

      <div ref={feedRef} onScroll={onScroll} className="flex-1 space-y-3 overflow-y-auto px-3 py-3">
        {feed.length === 0 && pending === null && (
          <div className="mt-10 text-center text-[12px] text-neutral-500">Ask Chief anything. Conversations stay on this Mac.</div>
        )}
        {feed}
        {pending !== null && (
          <div className="space-y-2">
            <div className="flex justify-end">
              <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-sky-600/70 px-3 py-2 text-[13px] text-white">
                {pending}
              </div>
            </div>
            <div className="text-[12px] text-neutral-500">Thinking…</div>
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-neutral-200 px-3 pb-3 pt-2 dark:border-neutral-800">
        <div className="mb-2 flex items-center gap-2">
          <button
            type="button"
            disabled={stopped === null}
            onClick={() => void toggleKillSwitch()}
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium disabled:opacity-40 ${
              stopped ? "bg-emerald-600 text-white hover:bg-emerald-700" : "bg-neutral-200 text-neutral-700 hover:bg-red-100 hover:text-red-700 dark:bg-neutral-800 dark:text-neutral-300"
            }`}
          >
            {stopped ? <PlayIcon /> : <StopIcon />}
            {stopped ? "Resume" : "Stop"}
          </button>
          <div className="flex-1" />
          <button
            type="button"
            disabled
            className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-neutral-400 disabled:cursor-not-allowed"
          >
            <ExpandIcon /> Workbench (coming later)
          </button>
        </div>
        <textarea
          ref={inputRef}
          rows={1}
          value={asking ? "" : input}
          placeholder={asking ? "Thinking…" : "Ask Chief…  (Enter to send, Shift-Enter for a new line)"}
          disabled={asking}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          maxLength={4000}
          autoFocus
          className="selectable block w-full resize-none rounded-xl border border-neutral-300 bg-white px-3 py-2 text-[13px] leading-5 outline-none placeholder:text-neutral-400 focus:border-sky-500 disabled:bg-neutral-100 dark:border-neutral-700 dark:bg-neutral-950 dark:disabled:bg-neutral-900"
        />
      </div>
    </div>
  );
}
