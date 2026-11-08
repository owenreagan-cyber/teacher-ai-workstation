import fs from "node:fs";
import path from "node:path";
import { homedir } from "node:os";

export type PidRecord = { pid: number; host: string; port: number; started_at: string; service: string };

const TOKEN_RE = /^[0-9a-f]{64}$/i;

export function expandHome(p: string): string {
  return p.startsWith("~/") ? path.join(homedir(), p.slice(2)) : p;
}

export function cosdDir(stateRoot: string): string {
  return path.join(expandHome(stateRoot), "cosd");
}

export function readPidRecord(stateRoot: string): PidRecord | null {
  try {
    const raw = fs.readFileSync(path.join(cosdDir(stateRoot), "cosd.pid"), "utf-8");
    const data = JSON.parse(raw) as PidRecord;
    if (data?.service !== "cosd" || !Number.isInteger(data.pid) || !Number.isInteger(data.port)) return null;
    if (data.host !== "127.0.0.1" && data.host !== "localhost") return null;
    return data;
  } catch {
    return null;
  }
}

export function readDaemonToken(stateRoot: string): string | null {
  try {
    const tok = fs.readFileSync(path.join(cosdDir(stateRoot), "api.token"), "utf-8").trim();
    return tok && TOKEN_RE.test(tok) ? tok : null;
  } catch {
    return null;
  }
}

export function processAlive(pid: number): boolean {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}
