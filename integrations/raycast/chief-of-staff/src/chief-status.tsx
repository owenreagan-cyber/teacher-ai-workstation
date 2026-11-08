import { Action, ActionPanel, Detail, Icon } from "@raycast/api";
import { useCallback, useEffect, useState } from "react";
import { clientFromPreferences, connectionLabel } from "./lib/cosd-client";
import { stateDirFromPrefs } from "./lib/prefs";
import type { ConnectionSnapshot } from "./lib/types";
import { DisconnectedDetail } from "./disconnected";

export default function Command() {
  const client = clientFromPreferences(stateDirFromPrefs());
  const [md, setMd] = useState<string | null>(null);
  const [snap, setSnap] = useState<ConnectionSnapshot | null>(null);

  const load = useCallback(async () => {
    setMd(null);
    const conn = await client.connectionSnapshot();
    setSnap(conn);
    if (conn.state !== "CONNECTED") return;
    const [status, runtime] = await Promise.all([client.status(), client.runtimeSnapshot()]);
    const rt = runtime.ok ? runtime.body : {};
    const model = status ?? (typeof rt.model === "object" ? (rt.model as Record<string, unknown>) : {});
    const lines = [
      `# Chief of Staff runtime`,
      `**Connection:** ${connectionLabel(conn.state)}`,
      conn.daemon_version ? `**cosd:** ${conn.daemon_version}` : "",
      typeof rt.api_version === "string" ? `**API:** ${rt.api_version}` : "",
      typeof rt.uptime_s === "number" ? `**Uptime:** ${rt.uptime_s}s` : "",
      typeof rt.queue_paused === "boolean" ? `**Queue:** ${rt.queue_paused ? "paused" : "active"}` : "",
      "",
      "## Model",
      typeof model.model === "string" ? `**Selected:** ${model.model}` : "",
      model.ollama_reachable === true ? "**Ollama:** reachable" : model.ollama_reachable === false ? "**Ollama:** unreachable" : "",
      model.kill_switch === true ? `**Kill switch:** on (${String(model.kill_switch_reason ?? "")})` : "",
      "",
      "## Task counts",
      typeof rt.task_counts === "object" && rt.task_counts !== null
        ? Object.entries(rt.task_counts as Record<string, number>)
            .map(([k, v]) => `- ${k}: ${v}`)
            .join("\n")
        : "",
    ].filter(Boolean);
    setMd(lines.join("\n"));
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (snap && snap.state !== "CONNECTED") return <DisconnectedDetail snap={snap} />;

  return (
    <Detail
      isLoading={md === null}
      markdown={md ?? ""}
      actions={
        <ActionPanel>
          <Action title="Refresh" icon={Icon.ArrowClockwise} onAction={() => void load()} />
          <Action.CopyToClipboard title="Copy Status" content={md ?? ""} />
        </ActionPanel>
      }
    />
  );
}
