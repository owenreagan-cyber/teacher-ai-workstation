import http, { type ClientRequest } from "node:http";

import type { DaemonEndpoint } from "./client.js";
import { requestJson } from "./http.js";
import { readDaemonToken } from "./paths.js";

export type CosdStreamEvent = { id: number; type: string; ts: string; task_id?: string; title?: string };

export class CosdEventStream {
  private req: ClientRequest | null = null;
  private buffer = "";
  private onEvent: ((ev: CosdStreamEvent) => void) | null = null;
  private lastId = 0;

  connect(ep: DaemonEndpoint, token: string, onEvent: (ev: CosdStreamEvent) => void, since = 0): void {
    this.disconnect();
    this.onEvent = onEvent;
    this.lastId = since;
    this.req = http.request(
      {
        host: ep.host,
        port: ep.port,
        path: `/v1/events?since=${since}`,
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      },
      (res) => {
        res.setEncoding("utf8");
        res.on("data", (chunk: string) => this.feed(chunk));
        res.on("end", () => this.disconnect());
        res.on("error", () => this.disconnect());
      },
    );
    this.req.on("error", () => this.disconnect());
    this.req.end();
  }

  private feed(chunk: string) {
    this.buffer += chunk;
    let idx: number;
    while ((idx = this.buffer.indexOf("\n\n")) >= 0) {
      const block = this.buffer.slice(0, idx);
      this.buffer = this.buffer.slice(idx + 2);
      for (const line of block.split("\n")) {
        if (!line.startsWith("data: ")) continue;
        try {
          const ev = JSON.parse(line.slice(6)) as CosdStreamEvent;
          if (ev.id) this.lastId = Math.max(this.lastId, ev.id);
          this.onEvent?.(ev);
        } catch {
          // ignore malformed
        }
      }
    }
  }

  disconnect(): void {
    this.req?.destroy();
    this.req = null;
  }

  get lastEventId(): number {
    return this.lastId;
  }
}

export function tokenForStream(): string | null {
  return readDaemonToken();
}

export async function fetchRuntime(ep: DaemonEndpoint, token: string) {
  return requestJson(ep.host, ep.port, "/v1/runtime", { token });
}
