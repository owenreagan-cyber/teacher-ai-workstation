// The left rail: Chief mark and status, the pages (⌘1–⌘5), Settings, and a quiet Stop Chief.
// Collapsed (icons only) below RAIL_BREAKPOINT_PX and in Focus; every icon-only button keeps its
// name in aria-label.
import { type Page, RAIL_PAGES } from "../shared/layout";
import { AgentsIcon, ChatIcon, FilesIcon, MacIcon, PlayIcon, SettingsIcon, StopIcon, TodayIcon } from "./icons";
import type { Dot } from "./messages";

const ICONS: Record<Page, () => React.ReactNode> = {
  today: () => <TodayIcon />,
  chat: () => <ChatIcon />,
  agents: () => <AgentsIcon />,
  mac: () => <MacIcon />,
  files: () => <FilesIcon />,
  settings: () => <SettingsIcon />,
};

const DOT = { green: "bg-good", amber: "bg-warn animate-pulse", red: "bg-bad", gray: "bg-muted" } as const;

type Props = {
  collapsed: boolean;
  active: Page;
  dot: Dot;
  stopped: boolean | null;
  onPage: (page: Page) => void;
  onKillSwitch: () => void;
};

function RailButton(props: {
  label: string;
  shortcut?: string;
  icon: React.ReactNode;
  collapsed: boolean;
  active?: boolean;
  disabled?: boolean;
  note?: string;
  onClick: () => void;
}) {
  const name = props.note ? `${props.label} (${props.note})` : props.label;
  return (
    <button
      type="button"
      onClick={props.onClick}
      disabled={props.disabled}
      aria-label={props.collapsed ? name : undefined}
      aria-current={props.active ? "page" : undefined}
      title={props.shortcut ? `${name} · ${props.shortcut}` : name}
      className={`no-drag flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-[13px] transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
        props.collapsed ? "justify-center" : ""
      } ${props.active ? "bg-accent-soft font-medium text-accent" : "text-ink hover:bg-bg"}`}
    >
      <span className="shrink-0">{props.icon}</span>
      {!props.collapsed && (
        <>
          <span className="min-w-0 flex-1 truncate">{props.label}</span>
          {props.note && <span className="text-[12px] text-muted">{props.note}</span>}
        </>
      )}
    </button>
  );
}

export function Rail({ collapsed, active, dot, stopped, onPage, onKillSwitch }: Props) {
  return (
    <nav
      aria-label="Chief"
      data-collapsed={collapsed ? "true" : "false"}
      className={`drag flex h-full shrink-0 flex-col border-r border-line bg-surface pb-3 pt-[44px] ${collapsed ? "w-[60px] px-2" : "w-[208px] px-3"}`}
    >
      <div className={`mb-4 flex items-center gap-2 ${collapsed ? "justify-center" : "px-1"}`}>
        <span aria-hidden="true" className="flex h-7 w-7 items-center justify-center rounded-lg bg-ink font-mono text-[13px] font-semibold text-bg">C</span>
        {!collapsed && <span className="text-[14px] font-semibold">Chief</span>}
        <span className={`h-2 w-2 shrink-0 rounded-full ${DOT[dot.color]}`} role="status" aria-label={dot.label} title={dot.label} />
        {!collapsed && <span className="truncate text-[12px] text-muted">{dot.label}</span>}
      </div>
      <div className="space-y-0.5">
        {RAIL_PAGES.map((p, i) => (
          <RailButton
            key={p.page}
            label={p.label}
            shortcut={`⌘${i + 1}`}
            icon={ICONS[p.page]()}
            collapsed={collapsed}
            active={active === p.page}
            disabled={!p.enabled}
            note={p.enabled ? undefined : "later"}
            onClick={() => onPage(p.page)}
          />
        ))}
      </div>
      <div className="flex-1" />
      <div className="space-y-0.5">
        <RailButton label="Settings" icon={<SettingsIcon />} collapsed={collapsed} active={active === "settings"} onClick={() => onPage("settings")} />
        <button
          type="button"
          disabled={stopped === null}
          onClick={onKillSwitch}
          aria-label={stopped ? "Resume Chief" : "Stop Chief"}
          title={stopped ? "Resume Chief" : "Stop Chief: denies every model and tool call until you resume"}
          className={`no-drag flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[13px] disabled:opacity-50 ${collapsed ? "justify-center" : ""} ${
            stopped ? "font-medium text-good hover:bg-bg" : "text-muted hover:bg-bg hover:text-bad"
          }`}
        >
          {stopped ? <PlayIcon /> : <StopIcon />}
          {!collapsed && <span>{stopped ? "Resume Chief" : "Stop Chief"}</span>}
        </button>
      </div>
    </nav>
  );
}
