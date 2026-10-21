// Settings. General shows the window's own settings (owned by the main process).
import type { WindowState } from "../shared/types";

type Props = { windowState: WindowState | null; onWindowState: (state: WindowState) => void };

export function SettingsPage({ windowState, onWindowState }: Props) {
  const isProtected = windowState?.protected ?? true;
  return (
    <div className="mx-auto max-w-[760px] space-y-4 p-6">
      <h1 className="text-[22px] font-semibold">Settings</h1>
      <section aria-labelledby="settings-general" className="rounded-xl border border-line bg-surface p-4">
        <h2 id="settings-general" className="mb-3 text-[13px] font-semibold">General</h2>
        <label className="flex items-center justify-between gap-4 text-[13px]">
          <span>
            Screen protection
            <span className="block text-[12px] text-muted">Hides this window from screenshots and screen sharing.</span>
          </span>
          <input
            type="checkbox"
            checked={isProtected}
            disabled={windowState === null}
            onChange={() => void window.chief.setProtection(!isProtected).then(onWindowState)}
          />
        </label>
      </section>
    </div>
  );
}
