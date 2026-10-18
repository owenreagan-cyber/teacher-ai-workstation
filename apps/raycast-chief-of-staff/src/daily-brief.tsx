import { Action, ActionPanel, Detail } from "@raycast/api";
import { useEffect, useState } from "react";
import { BriefResult, dailyBrief } from "./cos";

export default function Command() {
  const [result, setResult] = useState<BriefResult | null>(null);
  useEffect(() => {
    dailyBrief().then(setResult);
  }, []);
  const text = result?.ok ? result.lines.join("\n") : "";
  const markdown =
    result === null
      ? "_Building today's brief…_"
      : result.ok
        ? "```\n" + text + "\n```"
        : `**Error:** ${result.error}`;
  return (
    <Detail
      isLoading={result === null}
      markdown={markdown}
      actions={
        result?.ok ? (
          <ActionPanel>
            <Action.CopyToClipboard title="Copy Brief" content={text} />
          </ActionPanel>
        ) : undefined
      }
    />
  );
}
