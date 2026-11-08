import { Action, ActionPanel, Detail, Form, Icon, showToast, Toast, useNavigation } from "@raycast/api";
import { useEffect, useRef, useState } from "react";
import { clientFromPreferences } from "./lib/cosd-client";
import { sessionIdFromPrefs, stateDirFromPrefs } from "./lib/prefs";
import type { AskSuccess, ApiError, ConnectionSnapshot } from "./lib/types";
import { DisconnectedDetail } from "./disconnected";

function renderAnswer(question: string, result: AskSuccess | ApiError | null): string {
  const header = `**${question}**\n\n`;
  if (result === null) return `${header}_Waiting for cosd…_`;
  if (!result.ok) return `${header}**Error:** ${result.error}`;
  const text = result.text ?? result.answer ?? "";
  const notices = (result.notices ?? []).map((n) => `> ${n}`).join("\n");
  const tools = (result.tools_used ?? []).join(", ") || "none";
  const model = result.fast_path ? "fast path" : (result.model ?? "?");
  return `${header}${text}\n\n${notices ? `${notices}\n\n` : ""}---\nTools: \`${tools}\` · Model: \`${model}\``;
}

function AnswerView({ question }: { question: string }) {
  const client = clientFromPreferences(stateDirFromPrefs());
  const sessionId = sessionIdFromPrefs();
  const abort = useRef<AbortController | null>(null);
  const [result, setResult] = useState<AskSuccess | ApiError | null>(null);

  useEffect(() => {
    abort.current = new AbortController();
    client.ask(question, sessionId, abort.current.signal).then(setResult);
    return () => abort.current?.abort();
  }, [question]);

  return (
    <Detail
      isLoading={result === null}
      markdown={renderAnswer(question, result)}
      actions={
        <ActionPanel>
          {result?.ok ? <Action.CopyToClipboard title="Copy Answer" content={result.text ?? result.answer ?? ""} /> : null}
          <Action title="Cancel" icon={Icon.XMarkCircle} onAction={() => abort.current?.abort()} />
        </ActionPanel>
      }
    />
  );
}

export default function Command() {
  const { push } = useNavigation();
  const [snap, setSnap] = useState<ConnectionSnapshot | null>(null);
  const client = clientFromPreferences(stateDirFromPrefs());

  useEffect(() => {
    client.connectionSnapshot().then(setSnap);
  }, []);

  if (snap && snap.state !== "CONNECTED") return <DisconnectedDetail snap={snap} />;

  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Ask"
            onSubmit={async (values: { question: string }) => {
              const q = values.question.trim();
              if (!q) {
                await showToast({ style: Toast.Style.Failure, title: "Enter a question" });
                return;
              }
              push(<AnswerView question={q} />);
            }}
          />
        </ActionPanel>
      }
    >
      <Form.TextArea id="question" title="Question" placeholder="What should I focus on today?" />
    </Form>
  );
}
