import { getPreferenceValues } from "@raycast/api";
import { expandHome } from "./paths";

const DEFAULT_STATE = "~/Library/Application Support/ChiefOfStaff";

export function stateDirFromPrefs(): string {
  const { stateDir } = getPreferenceValues<{ stateDir?: string }>();
  const raw = (stateDir ?? DEFAULT_STATE).trim() || DEFAULT_STATE;
  return expandHome(raw);
}

export function sessionIdFromPrefs(): string | null {
  const { sessionId } = getPreferenceValues<{ sessionId?: string }>();
  const s = (sessionId ?? "raycast").trim();
  if (!s || s.length > 40) return null;
  return s;
}
