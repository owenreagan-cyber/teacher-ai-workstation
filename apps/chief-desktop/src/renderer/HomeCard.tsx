import type { HomeCard } from "../shared/types";
import { cardView } from "../shared/homeCard";

// Home card state in the window. Display only: it is never saved into the session, and it
// renders only here, inside the content-protected window (never in the tray, a title, or a
// notification).
export type HomeState =
  | { state: "loading" }
  | { state: "ready"; card: HomeCard; lines: string[] }
  | { state: "error"; text: string };

type Props = {
  home: HomeState;
  expanded: boolean; // full brief lines shown under the card
  collapsed: boolean; // thin one-line header (after the first question)
  onToggle: () => void;
  onRetry: () => void;
};

const BOX = "no-drag w-full rounded-xl border border-neutral-300/70 bg-white/60 text-left dark:border-neutral-700 dark:bg-neutral-900/60";

export function HomeCardView({ home, expanded, collapsed, onToggle, onRetry }: Props) {
  if (home.state === "loading") {
    return <div className={`${BOX} px-3 py-2 text-[12px] text-neutral-500`}>Loading today…</div>;
  }
  if (home.state === "error") {
    return (
      <button type="button" onClick={onRetry} className={`${BOX} px-3 py-2 text-[12px] text-neutral-500`}>
        {home.text} <span className="text-sky-600 dark:text-sky-400">Retry</span>
      </button>
    );
  }
  const view = cardView(home.card);
  if (collapsed && !expanded) {
    return (
      <button type="button" onClick={onToggle} aria-expanded={false} title="Show today" className={`${BOX} flex items-center gap-2 px-3 py-1 text-[11.5px]`}>
        <span className="min-w-0 flex-1 truncate text-neutral-600 dark:text-neutral-300">{view.summary}</span>
        <span className="text-neutral-400">▾</span>
      </button>
    );
  }
  return (
    <button type="button" onClick={onToggle} aria-expanded={expanded} className={`${BOX} px-3 py-2`}>
      <div className="flex items-baseline gap-2">
        <span className="text-[13px] font-medium">{view.greeting}</span>
        <span className="flex-1 text-[11px] text-neutral-500">{view.date}</span>
        <span className="text-[10.5px] text-neutral-400">{expanded ? "Hide brief ▴" : "Full brief ▾"}</span>
      </div>
      <div className="mt-1 space-y-0.5 text-[12px] leading-5">
        {view.rows.map((row) => (
          <div key={row.key} className={`truncate ${row.muted ? "text-neutral-500" : ""}`}>
            {row.text}
          </div>
        ))}
      </div>
      {expanded && (
        <div className="selectable mt-2 border-t border-neutral-300/60 pt-2 text-[11.5px] leading-5 dark:border-neutral-700">
          {home.lines.map((line, i) => (
            <div key={i} className={`whitespace-pre-wrap ${i === 0 ? "font-medium" : ""}`}>
              {line}
            </div>
          ))}
        </div>
      )}
    </button>
  );
}
