import { Action, ActionPanel, Icon, List, showToast, Toast } from "@raycast/api";
import { useEffect, useState } from "react";
import { clientFromPreferences } from "./lib/cosd-client";
import { stateDirFromPrefs } from "./lib/prefs";
import type { CosdTask, TaskState } from "./lib/types";
import { DisconnectedDetail } from "./disconnected";

const STATES: (TaskState | "ALL")[] = ["ALL", "QUEUED", "RUNNING", "BLOCKED", "FAILED", "COMPLETED", "CANCELLED"];

function TaskDetail({ task }: { task: CosdTask }) {
  const client = clientFromPreferences(stateDirFromPrefs());
  const [history, setHistory] = useState<{ ts: string; event: string }[] | null>(null);

  useEffect(() => {
    client.taskHistory(task.id).then((res) => {
      setHistory(res.ok ? res.events : []);
    });
  }, [task.id]);

  const lines = [
    `# ${task.title}`,
    `**ID:** \`${task.id}\``,
    `**State:** ${task.state} · **Kind:** ${task.kind} · **Priority:** ${task.priority}`,
    `**Attempts:** ${task.attempt_count}`,
    task.blocked_reason ? `**Blocked:** ${task.blocked_reason}` : "",
    task.last_error ? `**Last error:** ${task.last_error}` : "",
    task.next_retry_at ? `**Next retry:** ${task.next_retry_at}` : "",
    `**Created:** ${task.created_at}`,
    `**Updated:** ${task.updated_at}`,
    "",
    "## History",
    ...(history ?? []).map((h) => `- ${h.ts} — ${h.event}`),
  ].filter(Boolean);

  return (
    <List.Item.Detail markdown={lines.join("\n")} isLoading={history === null} />
  );
}

export default function Command() {
  const client = clientFromPreferences(stateDirFromPrefs());
  const [snap, setSnap] = useState<Awaited<ReturnType<typeof client.connectionSnapshot>> | null>(null);
  const [filter, setFilter] = useState<TaskState | "ALL">("ALL");
  const [search, setSearch] = useState("");
  const [tasks, setTasks] = useState<CosdTask[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.connectionSnapshot().then(setSnap);
  }, []);

  useEffect(() => {
    if (snap?.state !== "CONNECTED") return;
    setLoading(true);
    client
      .listTasks({ state: filter === "ALL" ? undefined : filter, limit: 100 })
      .then((res) => {
        setTasks(res.ok ? res.tasks : []);
        setLoading(false);
      });
  }, [snap?.state, filter]);

  if (snap && snap.state !== "CONNECTED") return <DisconnectedDetail snap={snap} />;

  const shown = tasks.filter((t) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return t.title.toLowerCase().includes(q) || t.kind.toLowerCase().includes(q) || t.id.startsWith(q);
  });

  return (
    <List
      isLoading={loading}
      isShowingDetail
      searchText={search}
      onSearchTextChange={setSearch}
      searchBarPlaceholder="Search tasks…"
      searchBarAccessory={
        <List.Dropdown tooltip="Filter by state" storeValue onChange={(v) => setFilter(v as TaskState | "ALL")}>
          {STATES.map((s) => (
            <List.Dropdown.Item key={s} title={s} value={s} />
          ))}
        </List.Dropdown>
      }
    >
      {shown.map((task) => (
        <List.Item
          key={task.id}
          title={task.title}
          subtitle={task.kind}
          accessories={[{ text: task.state }, { date: new Date(task.updated_at) }]}
          detail={<TaskDetail task={task} />}
          actions={
            <ActionPanel>
              <Action.CopyToClipboard title="Copy Task ID" content={task.id} />
              {["QUEUED", "RUNNING", "BLOCKED"].includes(task.state) ? (
                <Action
                  title="Cancel Task"
                  icon={Icon.XMarkCircle}
                  onAction={async () => {
                    const res = await client.cancelTask(task.id, "raycast");
                    if (!res.ok) await showToast({ style: Toast.Style.Failure, title: res.error });
                    else await showToast({ style: Toast.Style.Success, title: "Cancelled" });
                  }}
                />
              ) : null}
              {["FAILED", "BLOCKED"].includes(task.state) ? (
                <Action
                  title="Retry Task"
                  icon={Icon.ArrowClockwise}
                  onAction={async () => {
                    const res = await client.retryTask(task.id);
                    if (!res.ok) await showToast({ style: Toast.Style.Failure, title: res.error });
                    else await showToast({ style: Toast.Style.Success, title: "Queued for retry" });
                  }}
                />
              ) : null}
            </ActionPanel>
          }
        />
      ))}
    </List>
  );
}
