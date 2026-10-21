// Settings. General shows the window's own settings (owned by the main process); weather places and
// search and model settings are read and written through `cos config get|set`, which validates every
// write against the config schema. The page shows what cos returns after each save, never its own guess.
import { useCallback, useEffect, useState } from "react";

import { type ConfigReport, KEEP_ALIVE_CHOICES, parsePlace, type PlaceDraft, placeKey, type PlaceValue, type SettableKey } from "../shared/settings";
import type { ConfigResult, WindowState } from "../shared/types";

export type SettingsBridge = {
  configGet: () => Promise<ConfigResult>;
  configSet: (key: string, value: unknown) => Promise<ConfigResult>;
  setProtection: (enabled: boolean) => Promise<WindowState>;
};

type Props = { windowState: WindowState | null; onWindowState: (state: WindowState) => void; bridge?: SettingsBridge; initial?: ConfigReport | null };

function Section(props: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section aria-labelledby={props.id} className="rounded-xl border border-line bg-surface p-4">
      <h2 id={props.id} className="mb-3 text-[13px] font-semibold">{props.title}</h2>
      <div className="space-y-3">{props.children}</div>
    </section>
  );
}

function Row(props: { label: string; note?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 text-[13px]">
      <span className="min-w-0">
        {props.label}
        {props.note && <span className="block text-[12px] text-muted">{props.note}</span>}
      </span>
      <span className="shrink-0">{props.children}</span>
    </div>
  );
}

const INPUT = "selectable rounded-md border border-line bg-bg px-2 py-1 text-[13px] outline-none focus:border-accent";
const BUTTON = "rounded-md border border-line px-2.5 py-1 text-[12px] font-medium text-accent hover:bg-accent-soft disabled:opacity-50";

function PlaceEditor(props: { initial: PlaceDraft; saving: boolean; saveLabel: string; onSave: (p: PlaceValue) => void; onCancel?: () => void }) {
  const [draft, setDraft] = useState(props.initial);
  const [error, setError] = useState<string | null>(null);
  const field = (k: keyof PlaceDraft, label: string, width: string) => (
    <label className="flex flex-col gap-0.5 text-[12px] text-muted">
      {label}
      <input className={`${INPUT} ${width}`} value={draft[k]} onChange={(e) => setDraft({ ...draft, [k]: e.target.value })} />
    </label>
  );
  return (
    <div className="flex flex-wrap items-end gap-2">
      {field("name", "Name", "w-[180px]")}
      {field("latitude", "Latitude", "w-[110px]")}
      {field("longitude", "Longitude", "w-[110px]")}
      <button
        type="button"
        className={BUTTON}
        disabled={props.saving}
        onClick={() => {
          const p = parsePlace(draft);
          if (typeof p === "string") setError(p);
          else {
            setError(null);
            props.onSave(p);
          }
        }}
      >
        {props.saveLabel}
      </button>
      {props.onCancel && <button type="button" className="rounded-md px-2 py-1 text-[12px] text-muted hover:text-ink" onClick={props.onCancel}>Cancel</button>}
      {error && <div role="alert" className="w-full text-[12px] text-bad">{error}</div>}
    </div>
  );
}

const draftOf = (p: PlaceValue): PlaceDraft => ({ name: p.name, latitude: String(p.latitude), longitude: String(p.longitude) });
const KEY_LABEL: Record<string, string> = { home: "Home", work: "Work" };

export function SettingsPage({ windowState, onWindowState, bridge, initial = null }: Props) {
  const chief: SettingsBridge = bridge ?? window.chief;
  const [report, setReport] = useState<ConfigReport | null>(initial);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [model, setModel] = useState(initial?.values.model ?? "");

  const load = useCallback(async () => {
    const res = await chief.configGet();
    if (res.ok) {
      setReport(res);
      setModel(res.values.model);
      setError(null);
    } else setError(res.error);
  }, [chief]);

  useEffect(() => {
    if (initial === null) void load();
  }, [initial, load]);

  const save = async (key: SettableKey, value: unknown): Promise<boolean> => {
    setSaving(true);
    try {
      const res = await chief.configSet(key, value);
      if (!res.ok) {
        setError(res.error); // cos's own words: which field is wrong and why
        return false;
      }
      setReport(res);
      setModel(res.values.model);
      setError(null);
      return true;
    } finally {
      setSaving(false);
    }
  };

  const v = report?.values;
  const places = v ? Object.entries(v.places) : [];
  const isProtected = windowState?.protected ?? true;

  return (
    <div className="mx-auto max-w-[760px] space-y-4 p-6">
      <h1 className="text-[22px] font-semibold">Settings</h1>
      {error && <div role="alert" className="rounded-lg border border-bad/40 bg-surface px-3 py-2 text-[13px] text-bad">{error}</div>}

      <Section id="settings-general" title="General">
        <Row label="Start at login" note="Change it from the Chief menu bar icon.">
          <span className="text-[13px] text-muted">{windowState?.startAtLogin === null || windowState === null ? "Unknown" : windowState.startAtLogin ? "On" : "Off"}</span>
        </Row>
        <Row label="Screen protection" note="Hides this window from screenshots and screen sharing.">
          <input
            type="checkbox"
            aria-label="Screen protection"
            checked={isProtected}
            disabled={windowState === null}
            onChange={() => void chief.setProtection(!isProtected).then(onWindowState)}
          />
        </Row>
        <Row label="Hotkey" note="Set in desktop.json.">
          <span className="font-mono text-[12px]">{windowState?.hotkey ? windowState.hotkey.replace("Alt", "Option") : "–"}</span>
        </Row>
        <Row label="Appearance">
          <span className="text-[13px] text-muted">Follows macOS</span>
        </Row>
      </Section>

      <Section id="settings-places" title="Weather places">
        {!v && !error && <div className="text-[13px] text-muted">Loading…</div>}
        {places.map(([key, p]) => (
          <div key={key} className="border-b border-line pb-3 last:border-b-0 last:pb-0">
            {editing === key ? (
              <PlaceEditor
                initial={draftOf(p)}
                saving={saving}
                saveLabel="Save"
                onCancel={() => setEditing(null)}
                onSave={async (np) => {
                  if (await save("places", { ...v!.places, [key]: np })) setEditing(null);
                }}
              />
            ) : (
              <div className="flex items-center gap-3 text-[13px]">
                <span className="w-[56px] shrink-0 text-[12px] text-muted">{KEY_LABEL[key] ?? key}</span>
                <span className="min-w-0 flex-1 truncate font-medium">{p.name}</span>
                <span className="font-mono text-[12px] text-muted">{p.latitude.toFixed(2)}, {p.longitude.toFixed(2)}</span>
                <button type="button" className={BUTTON} onClick={() => setEditing(key)} aria-label={`Edit ${p.name}`}>Edit</button>
              </div>
            )}
          </div>
        ))}
        {v && (adding ? (
          <PlaceEditor
            initial={{ name: "", latitude: "", longitude: "" }}
            saving={saving}
            saveLabel="Add"
            onCancel={() => setAdding(false)}
            onSave={async (np) => {
              const key = placeKey(np.name, Object.keys(v.places));
              if (await save("places", { ...v.places, [key]: np })) setAdding(false);
            }}
          />
        ) : (
          <button type="button" className={BUTTON} onClick={() => setAdding(true)} disabled={places.length >= 10}>Add a place</button>
        ))}
        <p className="text-[12px] text-muted">Type the coordinates yourself (for example from a map); Chief doesn't look places up.</p>
      </Section>

      <Section id="settings-search" title="Search and local model">
        <Row label="Auto web search" note="Questions that need the web are searched without typing “search”.">
          <input
            type="checkbox"
            aria-label="Auto web search"
            checked={v?.auto_search ?? false}
            disabled={!v || saving}
            onChange={() => v && void save("auto_search", !v.auto_search)}
          />
        </Row>
        <Row label="Search limits" note="Change these in config.json.">
          <span className="font-mono text-[12px]">{v ? `${v.search_daily_limit} a day · ${v.search_monthly_limit} a month` : "–"}</span>
        </Row>
        <Row label="Local model" note={v?.fallback_model ? `Fallback: ${v.fallback_model}` : undefined}>
          <span className="flex items-center gap-2">
            <input className={`${INPUT} w-[180px] font-mono`} aria-label="Local model name" value={model} disabled={!v} onChange={(e) => setModel(e.target.value)} />
            <button type="button" className={BUTTON} disabled={!v || saving || model.trim() === v?.model} onClick={() => void save("model", model.trim())}>Save</button>
          </span>
        </Row>
        <Row label="Keep the model loaded for" note="After the last question (0 unloads it right away).">
          <select
            className={INPUT}
            aria-label="Keep the model loaded for"
            value={v?.model_keep_alive ?? ""}
            disabled={!v || saving}
            onChange={(e) => void save("model_keep_alive", e.target.value)}
          >
            {v && !(KEEP_ALIVE_CHOICES as readonly string[]).includes(v.model_keep_alive) && <option value={v.model_keep_alive}>{v.model_keep_alive}</option>}
            {KEEP_ALIVE_CHOICES.map((c) => <option key={c} value={c}>{c === "0" ? "Unload right away" : c}</option>)}
          </select>
        </Row>
      </Section>

      <footer className="px-1 text-[12px] text-muted">
        These settings are saved in config.json in Chief's data folder{report ? ` (${report.path})` : ""}.
      </footer>
    </div>
  );
}
