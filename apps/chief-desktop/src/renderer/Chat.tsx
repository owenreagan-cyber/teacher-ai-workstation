// The conversation: turns as cos recorded them (with their response blocks), display-only cards
// (Daily Brief, errors), the input, starter buttons for an empty chat, and the Split / Focus / Hide
// control. Display only: App owns sending, and a starter or suggestion sends its text through the
// same ask path as typing.
import { useState } from "react";

import { searchAttribution } from "../shared/attribution";
import { type ChatMode, CHAT_MODES, STARTERS } from "../shared/layout";
import type { Turn } from "../shared/types";
import { BlockList } from "./Blocks";

// Display-only cards (Daily Brief, errors). Never saved into the session.
export type CardBody = { kind: "brief"; lines: string[] } | { kind: "error"; text: string };
export type Card = CardBody & { id: number; afterTurns: number };

export function copyText(text: string): boolean {
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

function AnswerFooter({ turn }: { turn: Pick<Turn, "fast_path" | "model" | "tools_used" | "total_ms"> }) {
  // Rendered only from the turn's JSON as cos returned it.
  const engine = turn.fast_path ? "fast path (no model)" : (turn.model ?? "model not reported");
  const tools = turn.tools_used.length ? turn.tools_used.join(", ") : "none";
  return (
    <div className="mt-1.5 text-[12px] leading-4 text-muted">
      {engine} · Tools: {tools} · {turn.total_ms} ms
    </div>
  );
}

function TurnView({ turn, busy, onSend }: { turn: Turn; busy: boolean; onSend: (message: string) => void }) {
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
        <div className="selectable max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-accent px-3 py-2 text-[13px] text-on-accent">
          {turn.question}
        </div>
      </div>
      <div className="flex justify-start">
        <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-line bg-surface px-3 py-2 text-[13px]">
          {turn.blocks.length > 0 ? (
            <BlockList blocks={turn.blocks} busy={busy} onSend={onSend} />
          ) : (
            <>
              <div className="selectable whitespace-pre-wrap break-words">{turn.answer}</div>
              {turn.notices.map((n, i) => (
                <div key={i} className="selectable mt-1 text-[12px] text-warn">
                  Note: {n}
                </div>
              ))}
            </>
          )}
          {searchAttribution(turn) && <div className="mt-1 text-[12px] font-medium text-muted">{searchAttribution(turn)}</div>}
          <div className="flex items-end justify-between gap-2">
            <AnswerFooter turn={turn} />
            <button
              type="button"
              onClick={onCopy}
              className="shrink-0 rounded px-1.5 text-[12px] text-muted hover:bg-bg hover:text-ink"
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
      <div className="selectable rounded-xl border border-line bg-surface px-3 py-2 text-[12px] leading-5">
        <div className="mb-1 text-[12px] font-medium uppercase tracking-wide text-muted">Daily Brief · not saved</div>
        {card.lines.map((line, i) => (
          <div key={i} className={`whitespace-pre-wrap ${i === 0 ? "font-medium" : ""}`}>
            {line}
          </div>
        ))}
      </div>
    );
  }
  return <div className="rounded-xl border border-warn/50 bg-warn-soft px-3 py-2 text-[12px] text-warn">{card.text}</div>;
}

export function ModeControl({ mode, onMode }: { mode: ChatMode; onMode: (mode: ChatMode) => void }) {
  const names: Record<ChatMode, string> = { split: "Split", focus: "Focus", hide: "Hide" };
  return (
    <div role="radiogroup" aria-label="Chat layout" className="no-drag flex rounded-lg border border-line bg-surface p-0.5">
      {CHAT_MODES.map((m) => (
        <button
          key={m}
          type="button"
          role="radio"
          aria-checked={mode === m}
          title={m === "hide" ? "Hide chat · ⌘\\" : `${names[m]} chat`}
          onClick={() => onMode(m)}
          className={`rounded-md px-2.5 py-0.5 text-[12px] ${mode === m ? "bg-accent text-on-accent" : "text-muted hover:text-ink"}`}
        >
          {names[m]}
        </button>
      ))}
    </div>
  );
}

type Props = {
  turns: Turn[];
  cards: Card[];
  pending: string | null;
  input: string;
  asking: boolean;
  focus: boolean; // centered ~780 px column
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  feedRef: React.RefObject<HTMLDivElement | null>;
  onScroll: () => void;
  onInput: (text: string) => void;
  onKeyDown: (e: React.KeyboardEvent<HTMLTextAreaElement>) => void;
  onSend: (message: string) => void;
};

export function ChatPanel(props: Props) {
  const { turns, cards, pending, input, asking, focus, inputRef, feedRef } = props;
  const feed: React.ReactNode[] = [];
  for (let i = 0; i <= turns.length; i++) {
    for (const card of cards.filter((c) => c.afterTurns === i)) feed.push(<CardView key={`c${card.id}`} card={card} />);
    if (i < turns.length) {
      feed.push(<TurnView key={`t${i}-${turns[i].ts}`} turn={turns[i]} busy={asking} onSend={props.onSend} />);
    }
  }
  const column = focus ? "mx-auto w-full max-w-[780px]" : "w-full";
  return (
    <section aria-label="Chat" className="flex h-full min-w-0 flex-col">
      <div ref={feedRef} onScroll={props.onScroll} className="flex-1 overflow-y-auto px-4 py-4">
        <div className={`${column} space-y-3`}>
          {feed.length === 0 && pending === null && (
            <div className="mt-8 space-y-3 text-center">
              <div className="text-[13px] text-muted">
                Ask Chief anything. Questions that need the web are searched automatically. Conversations stay on this Mac.
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {STARTERS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    disabled={asking}
                    onClick={() => props.onSend(s)}
                    className="rounded-full border border-accent/40 px-3 py-1 text-[13px] text-accent hover:bg-accent-soft disabled:opacity-40"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {feed}
          {pending !== null && (
            <div className="space-y-2">
              <div className="flex justify-end">
                <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-2xl rounded-br-md bg-accent/70 px-3 py-2 text-[13px] text-on-accent">
                  {pending}
                </div>
              </div>
              <div className="text-[12px] text-muted">Thinking…</div>
            </div>
          )}
        </div>
      </div>
      <div className="shrink-0 border-t border-line px-4 pb-4 pt-3">
        <div className={column}>
          <textarea
            ref={inputRef}
            rows={1}
            value={asking ? "" : input}
            aria-label="Message Chief"
            placeholder={asking ? "Thinking…" : "Ask Chief…  (Enter to send, Shift-Enter for a new line, ⌘K to come back here)"}
            disabled={asking}
            onChange={(e) => props.onInput(e.target.value)}
            onKeyDown={props.onKeyDown}
            maxLength={4000}
            className="selectable block w-full resize-none rounded-xl border border-line bg-surface px-3 py-2 text-[13px] leading-5 outline-none placeholder:text-muted focus:border-accent disabled:opacity-60"
          />
        </div>
      </div>
    </section>
  );
}
