import fs from "node:fs";
import path from "node:path";

import { COS_STATE_DIR } from "../config.js";

const PID_FILE = "cosd.pid";
const TOKEN_FILE = "api.token";

export type PidRecord = { pid: number; host: string; port: number; started_at: string; service: string };

function cosdDir(stateRoot = COS_STATE_DIR): string {
  return path.join(stateRoot, "cosd");
}

export function readPidRecord(stateRoot = COS_STATE_DIR): PidRecord | null {
  try {
    const raw = fs.readFileSync(path.join(cosdDir(stateRoot), PID_FILE), "utf-8");
    const data = JSON.parse(raw) as PidRecord;
    if (data?.service !== "cosd" || !Number.isInteger(data.pid) || !Number.isInteger(data.port)) return null;
    if (data.host !== "127.0.0.1" && data.host !== "localhost") return null;
    return data;
  } catch {
    return null;
  }
}

export function readDaemonToken(stateRoot = COS_STATE_DIR): string | null {
  try {
    const tok = fs.readFileSync(path.join(cosdDir(stateRoot), TOKEN_FILE), "utf-8").trim();
    return tok && /^[0-9a-f]{64}$/i.test(tok) ? tok : null;
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
