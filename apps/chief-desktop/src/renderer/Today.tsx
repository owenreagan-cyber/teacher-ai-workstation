// The Today page and the cards it shares with the Mac and Agents pages. Display only: every value
// comes from `cos home --json` (validated in src/shared/home.ts); the greeting and date come from the
// current time. A card past its interval says "Stale · last checked …" and fades its numbers.
import { useState } from "react";

import {
  type BuildsData,
  type CalendarData,
  dateLine,
  freshness,
  greetingFor,
  type HomeSnapshot,
  type MacData,
  type MacSample,
  type NeedAction,
  type NeedItem,
  type RemindersData,
  type Section,
  splitNeeds,
  type WeatherData,
} from "../shared/home";
import { WeatherIcon } from "./Blocks";

export type HomeState =
  | { state: "loading" }
  | { state: "ready"; snap: HomeSnapshot }
  | { state: "error"; text: string };

export type OnAction = (action: NeedAction) => void;

const deg = (v: number | null) => (v === null ? "–" : `${v}°`);
const num = (v: number | null, unit = "") => (v === null ? "–" : `${v}${unit}`);

export function Card(props: { title: string; extra?: React.ReactNode; children: React.ReactNode; className?: string; labelledBy?: string }) {
  const id = props.labelledBy ?? `card-${props.title.toLowerCase().replace(/\W+/g, "-")}`;
  return (
    <section aria-labelledby={id} className={`rounded-xl border border-line bg-surface p-4 ${props.className ?? ""}`}>
      <div className="mb-3 flex items-baseline gap-2">
        <h2 id={id} className="text-[13px] font-semibold">{props.title}</h2>
        <div className="flex-1" />
        {props.extra}
      </div>
      {props.children}
    </section>
  );
}

export function FreshnessLabel({ section, now }: { section: Section<unknown>; now: Date }) {
  const f = freshness(section, now);
  const tone = f.tone === "warn" ? "text-warn" : "text-muted";
  return <span className={`text-[12px] ${tone}`} data-stale={f.stale ? "true" : "false"}>{f.label}</span>;
}

/** Children shown faded when the section is past its interval (numbers stay visible). */
function Fresh({ section, now, children }: { section: Section<unknown>; now: Date; children: React.ReactNode }) {
  return <div className={freshness(section, now).fade ? "chief-faded" : ""}>{children}</div>;
}

function Unavailable({ section }: { section: Section<unknown> }) {
  const text = section.status === "updating" ? "Checking…" : (section.reason ?? "Unavailable");
  return <div className="text-[12px] text-muted">{text}</div>;
}

// ----------------------------------------------------------------------------- needs

function ActionButton({ action, onAction }: { action: NeedAction; onAction: OnAction }) {
  const [done, setDone] = useState(false);
  const label = action.type === "command" ? (done ? "Copied" : action.label) : action.label;
  return (
    <button
      type="button"
      onClick={() => {
        onAction(action);
        if (action.type === "command") {
          setDone(true);
          setTimeout(() => setDone(false), 1500);
        }
      }}
      title={action.type === "command" ? action.command : undefined}
      className="shrink-0 rounded-md border border-line px-2 py-0.5 text-[12px] text-accent hover:bg-accent-soft"
    >
      {label}
    </button>
  );
}

function NeedRow({ item, onAction }: { item: NeedItem; onAction: OnAction }) {
  return (
    <li className="flex items-start gap-3 py-2">
      <div className="min-w-0 flex-1">
        <div className="text-[13px] font-medium">{item.title}</div>
        <div className="selectable text-[12px] text-muted">{item.reason}</div>
      </div>
      {item.action && <ActionButton action={item.action} onAction={onAction} />}
    </li>
  );
}

function Count({ n, tone }: { n: number; tone: "warn" | "accent" }) {
  const cls = tone === "warn" ? "bg-warn-soft text-warn" : "bg-accent-soft text-accent";
  return <span className={`rounded-full px-2 text-[12px] font-semibold ${cls}`} aria-label={`${n} items`}>{n}</span>;
}

export function NeedsCards({ section, onAction }: { section: Section<{ items: NeedItem[] }>; onAction: OnAction }) {
  const [all, setAll] = useState(false);
  const items = section.data?.items ?? [];
  const { decisions, decisionCount, suggestions, info } = splitNeeds(items, all ? Number.MAX_SAFE_INTEGER : 5);
  const unavailable = section.data === null;
  return (
    <>
      <div className="grid grid-cols-1 gap-4 @xl:grid-cols-2">
        <section aria-labelledby="needs-decision" className="rounded-xl border border-line border-l-4 border-l-warn bg-surface p-4">
          <div className="mb-1 flex items-center gap-2">
            <h2 id="needs-decision" className="text-[13px] font-semibold text-warn">Needs your decision</h2>
            <Count n={decisionCount} tone="warn" />
          </div>
          {unavailable ? (
            <Unavailable section={section} />
          ) : decisions.length === 0 ? (
            <div className="py-2 text-[13px] text-muted">Nothing needs your decision.</div>
          ) : (
            <ul className="divide-y divide-line">
              {decisions.map((d) => <NeedRow key={d.id} item={d} onAction={onAction} />)}
            </ul>
          )}
          {decisionCount > 5 && (
            <button type="button" onClick={() => setAll((v) => !v)} className="mt-1 text-[12px] font-medium text-accent hover:underline">
              {all ? "Show fewer" : `View all ${decisionCount}`}
            </button>
          )}
        </section>
        <section aria-labelledby="needs-suggestion" className="rounded-xl border border-line border-l-4 border-l-accent bg-surface p-4">
          <div className="mb-1 flex items-center gap-2">
            <h2 id="needs-suggestion" className="text-[13px] font-semibold text-accent">Suggested next steps</h2>
            <Count n={suggestions.length} tone="accent" />
          </div>
          {unavailable ? (
            <Unavailable section={section} />
          ) : suggestions.length === 0 ? (
            <div className="py-2 text-[13px] text-muted">No suggestions right now.</div>
          ) : (
            <ul className="divide-y divide-line">
              {suggestions.map((s) => <NeedRow key={s.id} item={s} onAction={onAction} />)}
            </ul>
          )}
        </section>
      </div>
      {info.length > 0 && (
        <ul className="space-y-1 px-1" aria-label="Notes">
          {info.map((i) => (
            <li key={i.id} className="flex items-center gap-2 text-[12px] text-muted">
              <span>{i.title}</span>
              {i.action && <ActionButton action={i.action} onAction={onAction} />}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

// ----------------------------------------------------------------------------- weather

function shortDay(label: string): string {
  if (label === "today") return "Today";
  if (label === "tomorrow") return "Tmrw";
  return label.slice(0, 3);
}

export function WeatherCard({ section, now }: { section: Section<WeatherData>; now: Date }) {
  const w = section.data;
  return (
    <Card title={w?.place ? `Weather · ${w.place}` : "Weather"} extra={<FreshnessLabel section={section} now={now} />}>
      {!w ? (
        <Unavailable section={section} />
      ) : (
        <Fresh section={section} now={now}>
          <div className="flex flex-wrap items-center gap-x-8 gap-y-3">
            <div className="flex items-center gap-3">
              <WeatherIcon conditions={w.conditions} isDay={w.is_day} size={52} />
              <div>
                <div className="font-mono text-[40px] font-medium leading-none" aria-label={`${num(w.temp_f)} degrees`}>{deg(w.temp_f)}</div>
                <div className="mt-1 text-[13px] capitalize">{w.conditions}</div>
              </div>
            </div>
            <dl className="grid grid-cols-3 gap-x-6 text-[12px]">
              <dt className="text-muted">High</dt>
              <dt className="text-muted">Low</dt>
              <dt className="text-muted">Rain</dt>
              <dd className="font-mono text-[15px]">{deg(w.high_f)}</dd>
              <dd className="font-mono text-[15px]">{deg(w.low_f)}</dd>
              <dd className="font-mono text-[15px]">{num(w.rain_chance_pct, "%")}</dd>
            </dl>
          </div>
          {w.days.length > 0 && (
            <ol className="mt-4 grid grid-cols-7 gap-1 border-t border-line pt-3" aria-label="7-day forecast">
              {w.days.map((d) => (
                <li key={d.date} className="flex flex-col items-center gap-1 text-center">
                  <span className="text-[12px] text-muted">{shortDay(d.label)}</span>
                  <WeatherIcon conditions={d.conditions} isDay={true} size={24} />
                  <span className="font-mono text-[12px]">{deg(d.high_f)}</span>
                  <span className="font-mono text-[12px] text-muted">{deg(d.low_f)}</span>
                </li>
              ))}
            </ol>
          )}
        </Fresh>
      )}
    </Card>
  );
}

// ----------------------------------------------------------------------------- today (calendar + reminders)

export function CalendarCard(props: { calendar: Section<CalendarData>; reminders: Section<RemindersData>; now: Date }) {
  const { calendar, reminders, now } = props;
  const events = calendar.data?.events ?? [];
  return (
    <Card title="Today" extra={<FreshnessLabel section={calendar} now={now} />}>
      {!calendar.data ? (
        <Unavailable section={calendar} />
      ) : (
        <Fresh section={calendar} now={now}>
          {events.length === 0 ? (
            <div className="text-[13px] text-muted">Nothing scheduled</div>
          ) : (
            <ul className="space-y-2">
              {events.map((ev, i) => (
                <li key={i} className="flex items-baseline gap-3">
                  <span className="w-[68px] shrink-0 font-mono text-[12px] text-muted">{ev.all_day ? "All day" : (ev.start ?? "–")}</span>
                  {ev.course && (
                    <span className="shrink-0 rounded border border-line bg-bg px-1.5 font-mono text-[12px] font-medium">{ev.course}</span>
                  )}
                  <span className="selectable min-w-0 truncate text-[13px]">{ev.title}</span>
                </li>
              ))}
            </ul>
          )}
        </Fresh>
      )}
      <div className="mt-3 border-t border-line pt-2 text-[12px]">
        {reminders.data ? (
          <span className={reminders.data.overdue ? "text-warn" : "text-muted"}>{reminders.data.line}</span>
        ) : (
          <span className="text-muted">Reminders: {reminders.status === "updating" ? "checking…" : (reminders.reason ?? "unavailable")}</span>
        )}
      </div>
    </Card>
  );
}

// ----------------------------------------------------------------------------- mac

export function Sparkline({ values, label }: { values: (number | null)[]; label: string }) {
  const pts = values.map((v, i) => [i, v] as const).filter((p): p is readonly [number, number] => p[1] !== null);
  if (pts.length < 2) return <div className="h-[28px] text-[12px] text-muted">Trend builds as Chief watches</div>;
  const n = values.length - 1;
  const path = pts.map(([i, v]) => `${((i / n) * 100).toFixed(1)},${(28 - (Math.min(100, Math.max(0, v)) / 100) * 26 - 1).toFixed(1)}`).join(" ");
  return (
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" className="h-[28px] w-full text-accent" role="img" aria-label={label}>
      <polyline points={path} fill="none" stroke="currentColor" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function Tile(props: { label: string; value: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-line p-3">
      <div className="text-[12px] text-muted">{props.label}</div>
      <div className="font-mono text-[20px] font-medium">{props.value}</div>
      {props.children}
    </div>
  );
}

function battery(m: MacData): string {
  if (m.battery_pct === null) return "–";
  return `${m.battery_pct}%${m.power_source === "AC power" ? " · on power" : ""}`;
}

export function MacCard({ section, history, now }: { section: Section<MacData>; history: MacSample[]; now: Date }) {
  const m = section.data;
  const health = m ? (
    <span className={`text-[12px] font-medium ${m.health === "healthy" ? "text-good" : "text-warn"}`}>
      {m.health === "healthy" ? "Healthy" : "Needs attention"}
    </span>
  ) : null;
  return (
    <Card title="Mac" extra={<span className="flex items-baseline gap-3">{health}<FreshnessLabel section={section} now={now} /></span>}>
      {!m ? (
        <Unavailable section={section} />
      ) : (
        <Fresh section={section} now={now}>
          <div className="grid grid-cols-2 gap-3">
            <Tile label="Memory free" value={num(m.memory_free_pct, "%")}>
              <Sparkline values={history.map((s) => s.memory_free_pct)} label="Memory free, last 30 minutes" />
            </Tile>
            <Tile label="CPU load" value={num(m.cpu_load_pct, "%")}>
              <Sparkline values={history.map((s) => s.cpu_load_pct)} label="CPU load, last 30 minutes" />
            </Tile>
          </div>
          <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-[12px]">
            <dt className="text-muted">Disk free</dt>
            <dd className="font-mono">{m.disk_free_gb === null ? "–" : `${m.disk_free_gb} GB`}</dd>
            <dt className="text-muted">Battery</dt>
            <dd className="font-mono">{battery(m)}</dd>
            <dt className="text-muted">Loaded model</dt>
            <dd className="font-mono">{m.loaded_models === null ? "unknown" : m.loaded_models.length ? m.loaded_models.join(", ") : "none"}</dd>
            {m.uptime && (
              <>
                <dt className="text-muted">Uptime</dt>
                <dd className="font-mono">{m.uptime}</dd>
              </>
            )}
          </dl>
          {m.attention.length > 0 && (
            <ul className="mt-2 text-[12px] text-warn">
              {m.attention.map((a) => <li key={a}>{a}</li>)}
            </ul>
          )}
        </Fresh>
      )}
    </Card>
  );
}

// ----------------------------------------------------------------------------- agents and builds

export function AgentsCard() {
  return (
    <Card title="Agent activity">
      <p className="text-[13px] text-muted">
        No agents running. When Chief delegates work, each agent shows here with Working, Waiting or Done, and a Stop button.
      </p>
    </Card>
  );
}

export function BuildsCard({ section, now }: { section: Section<BuildsData>; now: Date }) {
  const items = section.data?.items ?? [];
  return (
    <Card title="Recent builds" extra={<FreshnessLabel section={section} now={now} />}>
      {!section.data ? (
        <Unavailable section={section} />
      ) : items.length === 0 ? (
        <div className="text-[13px] text-muted">No merges on main yet.</div>
      ) : (
        <Fresh section={section} now={now}>
          <ul className="space-y-1.5">
            {items.map((b) => (
              <li key={b.ref} className="flex items-baseline gap-2 text-[13px]">
                <span className="text-good" aria-hidden="true">●</span>
                <span className="min-w-0 flex-1 truncate">{b.title}</span>
                {b.pr !== null && <span className="font-mono text-[12px] text-muted">#{b.pr}</span>}
                <span className="font-mono text-[12px] text-muted">{b.ref}</span>
              </li>
            ))}
          </ul>
        </Fresh>
      )}
    </Card>
  );
}

// ----------------------------------------------------------------------------- the page

type TodayProps = {
  home: HomeState;
  now: Date;
  briefing: boolean;
  onBrief: () => void;
  onAction: OnAction;
  onRetry: () => void;
};

export function TodayPage({ home, now, briefing, onBrief, onAction, onRetry }: TodayProps) {
  const snap = home.state === "ready" ? home.snap : null;
  return (
    <div className="@container mx-auto max-w-[1100px] space-y-4 p-6">
      <header className="flex flex-wrap items-end gap-3">
        <div className="min-w-0 flex-1">
          <h1 className="text-[22px] font-semibold">{greetingFor(now)}</h1>
          <div className="text-[13px] text-muted">
            {dateLine(now)}
            {snap?.place ? ` · ${snap.place}` : ""}
          </div>
        </div>
        <button
          type="button"
          onClick={onBrief}
          disabled={briefing}
          className="rounded-lg bg-accent px-3 py-1.5 text-[13px] font-medium text-on-accent hover:opacity-90 disabled:opacity-50"
        >
          {briefing ? "Building brief…" : "Today's brief"}
        </button>
        <button
          type="button"
          disabled
          aria-describedby="dev-mode-note"
          className="rounded-lg border border-line px-3 py-1.5 text-[13px] text-muted disabled:cursor-not-allowed"
        >
          Dev Mode
        </button>
        <span id="dev-mode-note" className="w-full text-right text-[12px] text-muted sm:w-auto">coming with the Mac helper</span>
      </header>

      {home.state === "loading" && <div className="text-[13px] text-muted">Loading today…</div>}
      {home.state === "error" && (
        <div className="flex items-center gap-3 rounded-xl border border-line bg-surface p-4 text-[13px]">
          <span className="text-muted">{home.text}</span>
          <button type="button" onClick={onRetry} className="text-[13px] font-medium text-accent hover:underline">Retry</button>
        </div>
      )}
      {snap?.stopped && (
        <div className="rounded-xl border border-bad/40 bg-surface p-3 text-[13px] text-bad">Chief is stopped. Nothing refreshes until you resume.</div>
      )}

      {snap && (
        <>
          <NeedsCards section={snap.needs} onAction={onAction} />
          <WeatherCard section={snap.weather} now={now} />
          <div className="grid grid-cols-1 gap-4 @xl:grid-cols-2">
            <CalendarCard calendar={snap.calendar} reminders={snap.reminders} now={now} />
            <MacCard section={snap.mac} history={snap.mac_history} now={now} />
          </div>
          <div className="grid grid-cols-1 gap-4 @xl:grid-cols-2">
            <AgentsCard />
            <BuildsCard section={snap.builds} now={now} />
          </div>
        </>
      )}
    </div>
  );
}

export function MacPage({ home, now }: { home: HomeState; now: Date }) {
  return (
    <div className="mx-auto max-w-[800px] space-y-4 p-6">
      <h1 className="text-[22px] font-semibold">Mac</h1>
      {home.state === "ready" ? <MacCard section={home.snap.mac} history={home.snap.mac_history} now={now} /> : <div className="text-[13px] text-muted">Loading…</div>}
    </div>
  );
}

export function AgentsPage({ home, now }: { home: HomeState; now: Date }) {
  return (
    <div className="mx-auto max-w-[800px] space-y-4 p-6">
      <h1 className="text-[22px] font-semibold">Agents & builds</h1>
      <AgentsCard />
      {home.state === "ready" ? <BuildsCard section={home.snap.builds} now={now} /> : <div className="text-[13px] text-muted">Loading…</div>}
    </div>
  );
}
