import { Action, ActionPanel, Form, Icon, showHUD, showToast, Toast } from "@raycast/api";
import { randomUUID } from "node:crypto";
import { useEffect, useMemo, useState } from "react";
import { clientFromPreferences } from "./lib/cosd-client";
import { stateDirFromPrefs } from "./lib/prefs";
import { DisconnectedDetail } from "./disconnected";

const PRIORITIES: { id: string; label: string; value: number }[] = [
  { id: "low", label: "Low", value: 0 },
  { id: "normal", label: "Normal", value: 1 },
  { id: "high", label: "High", value: 2 },
  { id: "urgent", label: "Urgent", value: 3 },
];

const DATA_CLASS = ["public", "internal", "sensitive"] as const;

export default function Command() {
  const client = clientFromPreferences(stateDirFromPrefs());
  const idemKey = useMemo(() => randomUUID(), []);
  const [snap, setSnap] = useState<Awaited<ReturnType<typeof client.connectionSnapshot>> | null>(null);

  useEffect(() => {
    client.connectionSnapshot().then(setSnap);
  }, []);

  if (snap && snap.state !== "CONNECTED") return <DisconnectedDetail snap={snap} />;

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Capture"
            icon={Icon.Plus}
            onSubmit={async (values: { title: string; description: string; priority: string; data_class: string }) => {
              const title = values.title.trim();
              if (!title) {
                await showToast({ style: Toast.Style.Failure, title: "Title required" });
                return;
              }
              const priority = PRIORITIES.find((p) => p.id === values.priority)?.value ?? 1;
              const data_class = DATA_CLASS.includes(values.data_class as (typeof DATA_CLASS)[number])
                ? values.data_class
                : "internal";
              const res = await client.createTask({
                kind: "capture",
                title,
                description: values.description?.trim() ?? "",
                priority,
                data_class,
                source: "raycast",
                requested_by: "raycast",
                idempotency_key: idemKey,
                payload: {},
              });
              if (!res.ok) {
                await showToast({ style: Toast.Style.Failure, title: "Capture failed", message: res.error });
                return;
              }
              const msg = res.reused ? "Existing task (idempotent)" : "Task captured";
              await showHUD(`${msg}: ${res.task.id.slice(0, 8)}…`);
              await showToast({
                style: Toast.Style.Success,
                title: msg,
                message: `${res.task.title} · ${res.task.state}`,
              });
            }}
          />
        </ActionPanel>
      }
    >
      <Form.TextField id="title" title="Title" placeholder="Follow up with curriculum lead" />
      <Form.TextArea id="description" title="Details" placeholder="Optional notes (not executed automatically)" />
      <Form.Dropdown id="priority" title="Priority" defaultValue="normal">
        {PRIORITIES.map((p) => (
          <Form.Dropdown.Item key={p.id} value={p.id} title={p.label} />
        ))}
      </Form.Dropdown>
      <Form.Dropdown id="data_class" title="Data class" defaultValue="internal">
        <Form.Dropdown.Item value="internal" title="Internal" />
        <Form.Dropdown.Item value="public" title="Public" />
        <Form.Dropdown.Item value="sensitive" title="Sensitive" />
      </Form.Dropdown>
    </Form>
  );
}
