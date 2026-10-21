// Renders response blocks (docs/response-blocks.md). Display only: every value comes from cos, the
// renderer never receives a URL (sources carry link ids; window.chief.openLink opens one), and a
// suggestion button sends its message text through the normal ask path, nothing else.
// Inline SVG and CSS only: no network, no image files, no chart or icon library.
import { useState } from "react";

import { type Block, type DailyPoint, type HourlyPoint, suggestionMessage, type WeatherNowBlock } from "../shared/blocks";

type Props = { blocks: Block[]; busy: boolean; onSend: (message: string) => void };

const deg = (v: number | null) => (v === null ? "–" : `${v}°`);

// ----------------------------------------------------------------------------- weather icon

type Sky = "clear" | "partly" | "cloud" | "rain" | "storm" | "snow" | "fog";

export function sky(conditions: string): Sky {
  const c = conditions.toLowerCase();
  if (c.includes("thunder")) return "storm";
  if (c.includes("snow")) return "snow";
  if (c.includes("rain") || c.includes("drizzle") || c.includes("shower")) return "rain";
  if (c.includes("fog")) return "fog";
  if (c.includes("overcast")) return "cloud";
  if (c.includes("partly") || c.includes("mostly")) return "partly";
  if (c.includes("clear") || c.includes("sunny")) return "clear";
  return "cloud";
}

export function WeatherIcon({ conditions, isDay, size = 40 }: { conditions: string; isDay: boolean | null; size?: number }) {
  const kind = sky(conditions);
  const night = isDay === false;
  const sun = night ? (
    <path d="M23 10a9 9 0 1 0 9 12 7 7 0 0 1-9-12Z" fill="#e6e1c5" />
  ) : (
    <g stroke="#f5b62d" strokeWidth="2" strokeLinecap="round">
      <circle cx="20" cy="18" r="7" fill="#f8c544" stroke="none" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => (
        <line key={a} x1="20" y1="5" x2="20" y2="8" transform={`rotate(${a} 20 18)`} />
      ))}
    </g>
  );
  const cloud = <path d="M14 34h17a7 7 0 0 0 0-14 9 9 0 0 0-17 2 6 6 0 0 0 0 12Z" fill={night ? "#9aa4b5" : "#d9dee6"} />;
  return (
    <svg width={size} height={size} viewBox="0 0 40 40" role="img" aria-label={conditions}>
      {(kind === "clear" || kind === "partly") && sun}
      {kind !== "clear" && cloud}
      {kind === "rain" && (
        <g className="chief-rain" stroke="#4f8fe0" strokeWidth="2" strokeLinecap="round">
          <line x1="17" y1="36" x2="15" y2="39" />
          <line x1="23" y1="36" x2="21" y2="39" />
          <line x1="29" y1="36" x2="27" y2="39" />
        </g>
      )}
      {kind === "storm" && <path d="m22 33-4 6h4l-2 4 6-7h-4l2-3Z" fill="#f2a93b" />}
      {kind === "snow" && (
        <g fill="#ffffff" stroke="#9fb6d6">
          <circle cx="17" cy="37" r="1.5" />
          <circle cx="24" cy="38" r="1.5" />
        </g>
      )}
      {kind === "fog" && (
        <g stroke="#b4bac4" strokeWidth="2" strokeLinecap="round">
          <line x1="10" y1="37" x2="30" y2="37" />
        </g>
      )}
    </svg>
  );
}

// Card backgrounds: warm daylight for sun, grey-blue for cloud, deep blue for rain, navy at night,
// an amber edge for storms. Light and dark appearance both read.
function cardClass(b: WeatherNowBlock): string {
  const kind = sky(b.conditions);
  if (b.is_day === false) return "from-indigo-950 to-slate-800 text-slate-100";
  if (kind === "storm") return "from-slate-600 to-slate-800 text-white ring-1 ring-amber-400/60";
  if (kind === "rain") return "from-sky-700 to-blue-900 text-white";
  if (kind === "cloud" || kind === "fog") return "from-slate-300 to-slate-400 text-slate-900 dark:from-slate-600 dark:to-slate-700 dark:text-slate-50";
  return "from-amber-200 to-sky-300 text-slate-900 dark:from-amber-700/70 dark:to-sky-800 dark:text-slate-50";
}

function WeatherNow({ b }: { b: WeatherNowBlock }) {
  return (
    <div className={`rounded-xl bg-gradient-to-br px-3 py-2 ${cardClass(b)}`}>
      <div className="flex items-center gap-2">
        <WeatherIcon conditions={b.conditions} isDay={b.is_day} />
        <div className="min-w-0 flex-1">
          <div className="truncate text-[12px] opacity-80">{b.place}</div>
          <div className="text-[22px] font-semibold leading-6">{deg(b.temp_f)}</div>
          <div className="text-[12px] capitalize opacity-90">{b.conditions}</div>
        </div>
        <div className="text-right text-[12px] leading-4 opacity-90">
          <div>H {deg(b.high_f)} · L {deg(b.low_f)}</div>
          <div>Rain {b.rain_chance_pct ?? "–"}%</div>
          {b.feels_like_f !== null && <div>Feels {deg(b.feels_like_f)}</div>}
        </div>
      </div>
    </div>
  );
}

function HourlyChart({ place, points }: { place: string; points: HourlyPoint[] }) {
  const w = 300, h = 96, top = 14, bottom = 18, step = w / points.length;
  const temps = points.map((p) => p.temp_f).filter((t): t is number => t !== null);
  const lo = Math.min(...temps), hi = Math.max(...temps);
  const y = (t: number) => top + (h - top - bottom) * (hi === lo ? 0.5 : 1 - (t - lo) / (hi - lo));
  const line = points
    .map((p, i) => (p.temp_f === null ? null : `${i === 0 ? "M" : "L"}${(i + 0.5) * step},${y(p.temp_f)}`))
    .filter(Boolean)
    .join(" ");
  const label = `Next ${points.length} hours in ${place}: ` + points.map((p) => `${p.time} ${deg(p.temp_f)}, rain ${p.rain_chance_pct ?? "–"}%`).join("; ");
  return (
    <figure className="rounded-xl border border-line px-2 py-1">
      <figcaption className="text-[12px] text-muted">Next {points.length} hours · temperature and rain chance</figcaption>
      <svg viewBox={`0 0 ${w} ${h}`} className="block w-full" role="img" aria-label={label}>
        {points.map((p, i) => (
          <rect key={`r${i}`} x={i * step + step * 0.2} width={step * 0.6} y={h - bottom - ((p.rain_chance_pct ?? 0) / 100) * 30}
            height={((p.rain_chance_pct ?? 0) / 100) * 30} rx="1.5" className="fill-sky-500/40" />
        ))}
        <path d={line} fill="none" strokeWidth="2" strokeLinejoin="round" className="stroke-amber-500" />
        {points.map((p, i) =>
          p.temp_f === null || i % 3 !== 0 ? null : (
            <text key={`t${i}`} x={(i + 0.5) * step} y={y(p.temp_f) - 4} textAnchor="middle" className="fill-ink text-[12px]">
              {deg(p.temp_f)}
            </text>
          ),
        )}
        {points.map((p, i) =>
          i % 3 !== 0 ? null : (
            <text key={`h${i}`} x={(i + 0.5) * step} y={h - 4} textAnchor="middle" className="fill-muted text-[12px]">
              {p.time}
            </text>
          ),
        )}
      </svg>
    </figure>
  );
}

function DailyForecast({ place, days }: { place: string; days: DailyPoint[] }) {
  const lows = days.map((d) => d.low_f).filter((t): t is number => t !== null);
  const highs = days.map((d) => d.high_f).filter((t): t is number => t !== null);
  const lo = Math.min(...lows), hi = Math.max(...highs), span = Math.max(1, hi - lo);
  return (
    <div className="rounded-xl border border-line px-2 py-1" aria-label={`Forecast for ${place}`}>
      {days.map((d) => (
        <div key={d.date} className="flex items-center gap-2 py-0.5 text-[12px]">
          <span className="w-[68px] truncate capitalize">{d.label}</span>
          <WeatherIcon conditions={d.conditions} isDay={true} size={18} />
          <span className="w-7 text-right text-muted">{deg(d.low_f)}</span>
          <span className="relative h-1.5 flex-1 rounded-full bg-line">
            {d.low_f !== null && d.high_f !== null && (
              <span className="absolute h-1.5 rounded-full bg-gradient-to-r from-sky-400 to-amber-400"
                style={{ left: `${((d.low_f - lo) / span) * 100}%`, width: `${Math.max(4, ((d.high_f - d.low_f) / span) * 100)}%` }} />
            )}
          </span>
          <span className="w-7">{deg(d.high_f)}</span>
          <span className="w-8 text-right text-[12px] text-accent">{d.rain_chance_pct ?? "–"}%</span>
        </div>
      ))}
    </div>
  );
}

function Sources({ items }: { items: Extract<Block, { type: "sources" }>["items"] }) {
  const [failed, setFailed] = useState(false);
  return (
    <details className="text-[12px]">
      <summary className="cursor-pointer text-muted">Sources ({items.length})</summary>
      <ol className="mt-1 space-y-0.5 pl-4">
        {items.map((it, i) => (
          <li key={i} className="list-decimal">
            {it.link_id ? (
              <button type="button" className="text-left text-accent underline-offset-2 hover:underline"
                onClick={() => void window.chief.openLink(it.link_id as string).then((r) => setFailed(!r.ok))}>
                {it.title}
              </button>
            ) : (
              <span>{it.title}</span>
            )}{" "}
            <span className="text-muted">· {it.site}</span>
          </li>
        ))}
      </ol>
      {failed && <div className="text-warn">That link couldn't be opened.</div>}
    </details>
  );
}

export function BlockList({ blocks, busy, onSend }: Props) {
  return (
    <div className="space-y-2">
      {blocks.map((b, i) => {
        switch (b.type) {
          case "text":
            return <div key={i} className="selectable whitespace-pre-wrap break-words">{b.text}</div>;
          case "weather_now":
            return <WeatherNow key={i} b={b} />;
          case "forecast_hourly":
            return <HourlyChart key={i} place={b.place} points={b.points} />;
          case "forecast_daily":
            return <DailyForecast key={i} place={b.place} days={b.days} />;
          case "sources":
            return <Sources key={i} items={b.items} />;
          case "searched":
            return <div key={i} className="selectable text-[12px] text-muted">Searched: {b.query}</div>;
          case "notice":
            return (
              <div key={i} className={`selectable text-[12px] ${b.level === "warning" ? "text-warn" : "text-muted"}`}>
                Note: {b.text}
              </div>
            );
          case "suggestions":
            return (
              <div key={i} className="flex flex-wrap gap-1.5">
                {b.items.map((it, j) => (
                  <button key={j} type="button" disabled={busy}
                    onClick={() => { const m = suggestionMessage(b, j); if (m !== null) onSend(m); }}
                    className="rounded-full border border-accent/40 px-2.5 py-0.5 text-[12px] text-accent hover:bg-accent-soft disabled:opacity-40">
                    {it.label}
                  </button>
                ))}
              </div>
            );
          default:
            return null;
        }
      })}
    </div>
  );
}
