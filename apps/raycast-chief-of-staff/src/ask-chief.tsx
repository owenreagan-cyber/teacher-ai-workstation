import { Action, ActionPanel, Detail, Form, LaunchProps, useNavigation } from "@raycast/api";
import { useEffect, useState } from "react";
import { AskResult, askChief } from "./cos";

function render(question: string, result: AskResult | null): string {
  const header = `**${question}**\n\n`;
  if (result === null) return `${header}_Thinking on the local model…_`;
  if (!result.ok) return `${header}**Error:** ${result.error}`;
  const notices = result.notices.map((n) => `> Note: ${n}`).join("\n");
  const tools = result.tools_used.length ? result.tools_used.join(", ") : "none";
  return `${header}${result.answer}\n\n${notices ? `${notices}\n\n` : ""}---\nTools used: \`${tools}\` · Model: \`${result.model ?? "?"}\``;
}

function AnswerView({ question }: { question: string }) {
  const [result, setResult] = useState<AskResult | null>(null);
  useEffect(() => {
    askChief(question).then(setResult);
  }, [question]);
  return (
    <Detail
      isLoading={result === null}
      markdown={render(question, result)}
      actions={
        result?.ok ? (
          <ActionPanel>
            <Action.CopyToClipboard title="Copy Answer" content={result.answer} />
          </ActionPanel>
        ) : undefined
      }
    />
  );
}

export default function Command(props: LaunchProps<{ arguments: { question?: string } }>) {
  const { push } = useNavigation();
  const initial = props.arguments.question?.trim();
  if (initial) return <AnswerView question={initial} />;
  return (
    <Form
      actions={
        <ActionPanel>
          <Action.SubmitForm
            title="Ask"
            onSubmit={(values: { question: string }) => {
              const q = values.question.trim();
              if (q) push(<AnswerView question={q} />);
            }}
          />
        </ActionPanel>
      }
    >
      <Form.TextArea id="question" title="Ask Chief" placeholder="What's on my calendar today?" />
    </Form>
  );
}
