// Loopback-only HTTP for cosd (main process). No fetch; host must be 127.0.0.1 or localhost.
import http from "node:http";

const MAX_RESPONSE_BYTES = 2_000_000;

export class CosdHttpError extends Error {
  constructor(
    message: string,
    readonly kind: string = "internal",
  ) {
    super(message);
  }
}

function assertLoopback(host: string): void {
  if (host !== "127.0.0.1" && host !== "localhost") {
    throw new CosdHttpError("refusing non-loopback cosd endpoint", "usage");
  }
}

export function requestJson(
  host: string,
  port: number,
  path: string,
  options: {
    method?: string;
    body?: unknown;
    token?: string;
    timeoutMs?: number;
  } = {},
): Promise<{ status: number; body: Record<string, unknown> }> {
  assertLoopback(host);
  const method = options.method ?? "GET";
  const payload = options.body !== undefined ? JSON.stringify(options.body) : undefined;
  const headers: Record<string, string> = {};
  if (payload !== undefined) {
    headers["Content-Type"] = "application/json";
    headers["Content-Length"] = String(Buffer.byteLength(payload));
  }
  if (options.token) headers.Authorization = `Bearer ${options.token}`;

  return new Promise((resolve, reject) => {
    const req = http.request(
      { host, port, path, method, headers, family: 4 },
      (res) => {
        const chunks: Buffer[] = [];
        let size = 0;
        res.on("data", (chunk: Buffer) => {
          size += chunk.length;
          if (size > MAX_RESPONSE_BYTES) {
            req.destroy();
            reject(new CosdHttpError("response too large", "internal"));
            return;
          }
          chunks.push(chunk);
        });
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf-8");
          try {
            const body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
            resolve({ status: res.statusCode ?? 0, body });
          } catch {
            reject(new CosdHttpError("invalid JSON from cosd", "internal"));
          }
        });
      },
    );
    req.on("error", () => reject(new CosdHttpError("cosd unreachable", "unavailable")));
    const t = setTimeout(() => {
      req.destroy();
      reject(new CosdHttpError("cosd request timed out", "timeout"));
    }, options.timeoutMs ?? 10_000);
    req.on("close", () => clearTimeout(t));
    if (payload !== undefined) req.write(payload);
    req.end();
  });
}

export function requestAskNdjsonStream(
  host: string,
  port: number,
  token: string,
  question: string,
  sessionId: string | null,
  onChunk: (text: string) => void,
  signal: AbortSignal | undefined,
  timeoutMs: number,
): Promise<Record<string, unknown>> {
  assertLoopback(host);
  if (signal?.aborted) throw new CosdHttpError("cancelled", "usage");
  const payload = JSON.stringify({ question, ...(sessionId ? { session_id: sessionId } : {}) });
  return new Promise((resolve, reject) => {
    const req = http.request(
      {
        host,
        port,
        path: "/v1/ask/stream",
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          "Content-Length": String(Buffer.byteLength(payload)),
        },
        family: 4,
      },
      (res) => {
        let buf = "";
        let size = 0;
        const fail = (msg: string) => reject(new CosdHttpError(msg, "internal"));
        res.setEncoding("utf8");
        res.on("data", (chunk: string) => {
          size += chunk.length;
          if (size > MAX_RESPONSE_BYTES) {
            req.destroy();
            fail("response too large");
            return;
          }
          buf += chunk;
          let nl: number;
          while ((nl = buf.indexOf("\n")) >= 0) {
            const line = buf.slice(0, nl).trim();
            buf = buf.slice(nl + 1);
            if (!line) continue;
            try {
              const item = JSON.parse(line) as Record<string, unknown>;
              if (item.type === "chunk" && typeof item.text === "string") onChunk(item.text);
              else if (item.type === "done") resolve(item);
              else if (item.type === "error") {
                const body = (item.body as Record<string, unknown>) ?? item;
                reject(new CosdHttpError(String(body.error ?? "ask failed"), String(body.error_kind ?? "internal")));
              }
            } catch {
              fail("invalid NDJSON from cosd");
            }
          }
        });
        res.on("end", () => {
          if (buf.trim()) {
            try {
              const item = JSON.parse(buf.trim()) as Record<string, unknown>;
              if (item.type === "done") resolve(item);
              return;
            } catch {
              fail("truncated stream");
              return;
            }
          }
          fail("empty stream");
        });
        res.on("error", () => reject(new CosdHttpError("cosd unreachable", "unavailable")));
      },
    );
    req.on("error", () => reject(new CosdHttpError("cosd unreachable", "unavailable")));
    const onAbort = () => {
      req.destroy();
      reject(new CosdHttpError("cancelled", "usage"));
    };
    signal?.addEventListener("abort", onAbort, { once: true });
    req.on("close", () => signal?.removeEventListener("abort", onAbort));
    const t = setTimeout(() => {
      req.destroy();
      reject(new CosdHttpError("cosd request timed out", "timeout"));
    }, timeoutMs);
    req.on("close", () => clearTimeout(t));
    req.write(payload);
    req.end();
  });
}
