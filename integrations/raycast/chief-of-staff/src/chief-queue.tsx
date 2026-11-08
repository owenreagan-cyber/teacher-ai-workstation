import { Action, ActionPanel, Icon, List } from "@raycast/api";
import { useEffect, useState } from "react";
import { clientFromPreferences } from "./lib/cosd-client";
import { stateDirFromPrefs } from "./lib/prefs";
import { DisconnectedDetail } from "./disconnected";

export default function Command() {
  const client = clientFromPreferences(stateDirFromPrefs());
  const [snap, setSnap] = useState<Awaited<ReturnType<typeof client.connectionSnapshot>> | null>(null);
  const [queue, setQueue] = useState<Awaited<ReturnType<typeof client.queueSnapshot>> | null>(null);
  const [workers, setWorkers] = useState<unknown[]>([]);
  const [running, setRunning] = useState<{ ok: true; tasks: import("./lib/types").CosdTask[] } | null>(null);

  useEffect(() => {
    (async () => {
      const s = await client.connectionSnapshot();
      setSnap(s);
      if (s.state !== "CONNECTED") return;
      const [q, w, run] = await Promise.all([
        client.queueSnapshot(),
        client.workers(),
        client.listTasks({ state: "RUNNING", limit: 50 }),
      ]);
      setQueue(q);
      setWorkers(w.ok ? w.workers : []);
      setRunning(run.ok ? { ok: true, tasks: run.tasks } : null);
    })();
  }, []);

  if (snap && snap.state !== "CONNECTED") return <DisconnectedDetail snap={snap} />;

  const counts = queue?.ok ? queue.task_counts : {};
  const paused = queue?.ok ? queue.paused : false;
  const leases = queue?.ok ? queue.active_leases.length : 0;

  return (
    <List isLoading={queue === null}>
      <List.Section title="Queue">
        <List.Item title={paused ? "Paused" : "Active"} icon={paused ? Icon.Pause : Icon.Play} />
        <List.Item title="Active worker leases" subtitle={String(leases)} icon={Icon.Person} />
        {Object.entries(counts).map(([state, n]) => (
          <List.Item key={state} title={state} subtitle={String(n)} icon={Icon.Circle} />
        ))}
      </List.Section>
      <List.Section title="Running tasks">
        {(running?.tasks ?? []).map((t) => (
          <List.Item key={t.id} title={t.title} subtitle={t.kind} accessories={[{ text: t.id.slice(0, 8) }]} />
        ))}
      </List.Section>
      <List.Section title="Workers">
        {workers.length === 0 ? (
          <List.Item title="No active workers" icon={Icon.Minus} />
        ) : (
          workers.map((w, i) => (
            <List.Item
              key={i}
              title={typeof w === "object" && w !== null && "worker_id" in w ? String((w as { worker_id: string }).worker_id) : `Worker ${i + 1}`}
              subtitle={JSON.stringify(w).slice(0, 120)}
              icon={Icon.Gear}
              actions={
                <ActionPanel>
                  <Action.CopyToClipboard title="Copy Worker JSON" content={JSON.stringify(w)} />
                </ActionPanel>
              }
            />
          ))
        )}
      </List.Section>
    </List>
  );
}
