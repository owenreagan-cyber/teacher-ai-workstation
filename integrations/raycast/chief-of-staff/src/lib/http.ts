import http from "node:http";

const MAX_BYTES = 2_000_000;

export class CosdHttpError extends Error {
  constructor(
    message: string,
    readonly kind: string = "internal",
  ) {
    super(message);
  }
}

export function assertLoopback(host: string): void {
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
    const req = http.request({ host, port, path, method, headers, family: 4 }, (res) => {
      const chunks: Buffer[] = [];
      let size = 0;
      res.on("data", (chunk: Buffer) => {
        size += chunk.length;
        if (size > MAX_BYTES) {
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
    });
    req.on("error", () => reject(new CosdHttpError("cosd unreachable", "unavailable")));
    const t = setTimeout(() => {
      req.destroy();
      reject(new CosdHttpError("cosd request timed out", "timeout"));
    }, options.timeoutMs ?? 15_000);
    req.on("close", () => clearTimeout(t));
    if (payload !== undefined) req.write(payload);
    req.end();
  });
}
