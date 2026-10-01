// Runs the local cos CLI and parses its JSON. No network access from the extension.
import { getPreferenceValues } from "@raycast/api";
import { execFile } from "node:child_process";
import { homedir } from "node:os";

export type AskResult =
  | {
      ok: true;
      answer: string;
      tools_used: string[];
      model: string | null;
      notices: string[];
      fast_path?: boolean;
    }
  | { ok: false; error: string };

export type BriefResult = { ok: true; lines: string[] } | { ok: false; error: string };

const ASK_TIMEOUT_MS = 300_000; // a cold 35B model load can take a while
const BRIEF_TIMEOUT_MS = 90_000;

function cosPath(): string {
  const { cosPath } = getPreferenceValues<{ cosPath: string }>();
  return cosPath.startsWith("~/") ? homedir() + cosPath.slice(1) : cosPath;
}

function runCos<T>(args: string[], timeoutMs: number): Promise<T> {
  return new Promise((resolve) => {
    execFile(cosPath(), args, { timeout: timeoutMs, maxBuffer: 1_000_000 }, (err, stdout, stderr) => {
      const text = stdout.trim();
      if (text) {
        try {
          resolve(JSON.parse(text) as T); // cos prints {"ok": false, ...} on handled errors too
          return;
        } catch {
          // fall through to the error below
        }
      }
      const detail = err ? `${err.message}${stderr ? `\n${stderr.trim()}` : ""}` : "cos returned no JSON";
      resolve({ ok: false, error: detail } as T);
    });
  });
}

export function askChief(question: string): Promise<AskResult> {
  return runCos<AskResult>(["ask", "--json", question], ASK_TIMEOUT_MS);
}

export function dailyBrief(): Promise<BriefResult> {
  return runCos<BriefResult>(["brief", "--json"], BRIEF_TIMEOUT_MS);
}
