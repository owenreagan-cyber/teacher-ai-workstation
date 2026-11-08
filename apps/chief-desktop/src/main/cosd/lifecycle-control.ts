import { execFile } from "node:child_process";
import path from "node:path";
import { promisify } from "node:util";

import { minimalEnv } from "../cos.js";

const execFileAsync = promisify(execFile);

export function cosdBinFromCos(cosPath: string): string {
  return path.join(path.dirname(cosPath), "cosd");
}

export async function cosdStart(cosdPath: string): Promise<{ ok: boolean; error?: string }> {
  try {
    await execFileAsync(cosdPath, ["start"], { env: minimalEnv(), timeout: 20_000 });
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "start failed" };
  }
}

export async function cosdStop(cosdPath: string): Promise<{ ok: boolean; error?: string }> {
  try {
    await execFileAsync(cosdPath, ["stop"], { env: minimalEnv(), timeout: 15_000 });
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "stop failed" };
  }
}

export async function cosdRestart(cosdPath: string): Promise<{ ok: boolean; error?: string }> {
  try {
    await execFileAsync(cosdPath, ["restart"], { env: minimalEnv(), timeout: 30_000 });
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "restart failed" };
  }
}
