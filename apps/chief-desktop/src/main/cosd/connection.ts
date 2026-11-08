import type { CosdConnectionSnapshot, CosdConnectionState, ExecutionMode } from "../../shared/cosd.js";
import { CosdClient, type DaemonEndpoint } from "./client.js";

export type DaemonMode = "auto" | "required" | "disabled";

export function daemonModeFromEnv(): DaemonMode {
  const raw = (process.env.CHIEF_USE_DAEMON ?? process.env.COS_USE_DAEMON ?? "auto").trim().toLowerCase();
  if (raw === "required" || raw === "disabled") return raw;
  return "auto";
}

type Listener = (snap: CosdConnectionSnapshot) => void;

export class CosdConnectionManager {
  private state: CosdConnectionState = "DISCONNECTED";
  private detail: string | null = null;
  private endpoint: DaemonEndpoint | null = null;
  private listeners = new Set<Listener>();
  private pollTimer: NodeJS.Timeout | null = null;
  private backoffMs = 2000;
  private readonly client = new CosdClient();

  constructor(private readonly onChange?: (snap: CosdConnectionSnapshot) => void) {}

  snapshot(): CosdConnectionSnapshot {
    return {
      state: this.state,
      execution_mode: this.executionMode(),
      detail: this.detail,
      daemon_version: this.endpoint?.version ?? null,
    };
  }

  executionMode(): ExecutionMode {
    const mode = daemonModeFromEnv();
    if (mode === "disabled") return "standalone";
    if (this.state === "CONNECTED") return "daemon";
    if (mode === "required") return "standalone";
    return "standalone";
  }

  getEndpoint(): DaemonEndpoint | null {
    return this.state === "CONNECTED" && this.endpoint ? this.endpoint : null;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot());
    return () => this.listeners.delete(listener);
  }

  private emit(): void {
    const snap = this.snapshot();
    for (const l of this.listeners) l(snap);
    this.onChange?.(snap);
  }

  private setState(state: CosdConnectionState, detail: string | null, endpoint: DaemonEndpoint | null = this.endpoint): void {
    this.state = state;
    this.detail = detail;
    this.endpoint = endpoint;
    this.emit();
  }

  async refresh(): Promise<CosdConnectionSnapshot> {
    const mode = daemonModeFromEnv();
    if (mode === "disabled") {
      this.setState("DISCONNECTED", "daemon client disabled", null);
      return this.snapshot();
    }
    this.setState(this.state === "CONNECTED" ? "RECOVERING" : "CONNECTING", null, null);
    try {
      const ep = await this.client.discover();
      if (!ep) {
        this.backoffMs = Math.min(this.backoffMs * 2, 60_000);
        this.setState("DISCONNECTED", "cosd is not running", null);
        return this.snapshot();
      }
      const authed = await this.client.probeAuth(ep);
      const state = this.client.connectionStateFromDiscover(ep, authed);
      this.backoffMs = 2000;
      this.setState(
        state,
        state === "AUTH_ERROR" ? "Authentication failed — try bin/cosd rotate-token" : state === "VERSION_MISMATCH" ? "cosd API version incompatible" : null,
        state === "CONNECTED" ? ep : null,
      );
    } catch {
      this.setState("DISCONNECTED", "Could not reach cosd", null);
    }
    return this.snapshot();
  }

  startPolling(intervalMs = 15_000): void {
    void this.refresh();
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(() => {
      void this.refresh();
    }, intervalMs);
  }

  stopPolling(): void {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = null;
  }
}
