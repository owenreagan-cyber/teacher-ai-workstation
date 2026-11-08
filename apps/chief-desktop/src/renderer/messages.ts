import type { ErrorKind, StatusResult } from "../shared/types";

// Fixed, friendly text per error kind. Raw errors and stack traces are never shown.
export function errorMessage(kind: ErrorKind, detail: string): string {
  switch (kind) {
    case "model_unavailable":
      return "Chief is running, but the local model isn't available. Open Ollama and try again.";
    case "stopped":
      return "Chief is stopped. Click Resume to continue.";
    case "setup":
      return `Chief isn't set up yet: ${detail}`; // a path or desktop.json problem, written by the shell
    case "timeout":
      return "Chief took too long to answer. Try again.";
    case "usage":
      return "That request couldn't be sent. Check the question and try again.";
    default:
      return "Something went wrong inside Chief. Try again.";
  }
}

export type Dot = { color: "green" | "amber" | "red" | "gray"; label: string };

// The dot reflects the latest cos status; amber only while a request is in flight.
export function statusDot(status: StatusResult | null, busy: boolean): Dot {
  if (busy) return { color: "amber", label: "Working" };
  if (status === null) return { color: "gray", label: "Checking" };
  if (!status.ok) return { color: "gray", label: "Chief unavailable" };
  if (status.cosd_connection === "AUTH_ERROR") return { color: "red", label: "cosd auth error" };
  if (status.cosd_connection === "DISCONNECTED" && status.execution_mode === "daemon") {
    return { color: "gray", label: "cosd disconnected" };
  }
  if (status.cosd_connection === "RECOVERING" || status.cosd_connection === "CONNECTING") {
    return { color: "amber", label: "Connecting to cosd" };
  }
  if (status.kill_switch) return { color: "red", label: "Stopped" };
  if (!status.ollama_reachable) return { color: "gray", label: "Local model unavailable" };
  if (status.via_daemon) return { color: "green", label: "Ready (cosd)" };
  return { color: "green", label: "Ready" };
}
