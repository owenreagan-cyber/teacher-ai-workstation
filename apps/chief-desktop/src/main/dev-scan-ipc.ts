// Development HQ scan: the IPC-facing handlers, kept free of Electron imports so they can be tested
// with fakes. main.ts wires each one to a fixed `chief:devscan-*` channel.
//
// Authorization boundary (all enforced here and again in cosd):
//  - the renderer sends one boolean (include processes) or a task id, never a path, kind, or limit;
//  - roots come only from the approved-roots file, which changes only via the native folder picker;
//  - the task kind and title are constants.
import type { DevScanRootsResult, DevScanRunResult } from "../shared/devscan.js";
import { addApprovedRoot, readApprovedRoots, removeApprovedRoot } from "./dev-scan.js";
import { validateDevScanRootPath, validateDevScanRun, validateTaskId } from "./ipc-cosd.js";

export type DevScanRuntime = {
  runDevScan(roots: string[], includeProcesses: boolean): Promise<DevScanRunResult>;
  executeDevScan(taskId: string): Promise<DevScanRunResult>;
  devScanReport(taskId: string): Promise<DevScanRunResult>;
};

export type DevScanHandlerDeps = {
  stateDir: string;
  runtime: DevScanRuntime;
  /** Native folder picker (main process). Resolves to the chosen folder, or null if canceled. */
  pickFolder: () => Promise<string | null>;
  home?: string;
};

const BUSY: DevScanRunResult = { ok: false, error: "A development scan is already running.", error_kind: "usage" };
const NO_ROOTS: DevScanRunResult = {
  ok: false,
  error: "Approve at least one development folder before scanning.",
  error_kind: "usage",
};

export function createDevScanHandlers(deps: DevScanHandlerDeps) {
  const home = deps.home === undefined ? undefined : { home: deps.home };
  let running = false;

  const guarded = async (work: () => Promise<DevScanRunResult>): Promise<DevScanRunResult> => {
    if (running) return BUSY;
    running = true;
    try {
      return await work();
    } finally {
      running = false;
    }
  };

  return {
    roots(): DevScanRootsResult {
      return { ok: true, roots: readApprovedRoots(deps.stateDir, home) };
    },

    async addRoot(): Promise<DevScanRootsResult> {
      const picked = await deps.pickFolder();
      if (picked === null) return { ok: true, roots: readApprovedRoots(deps.stateDir, home), canceled: true };
      const change = addApprovedRoot(deps.stateDir, picked, home);
      return change.ok ? { ok: true, roots: change.roots } : { ok: false, error: change.error, error_kind: "usage" };
    },

    removeRoot(rootPath: unknown): DevScanRootsResult {
      const change = removeApprovedRoot(deps.stateDir, validateDevScanRootPath(rootPath), home);
      return change.ok ? { ok: true, roots: change.roots } : { ok: false, error: change.error, error_kind: "usage" };
    },

    run(includeProcesses: unknown): Promise<DevScanRunResult> {
      const include = validateDevScanRun(includeProcesses);
      return guarded(async () => {
        const roots = readApprovedRoots(deps.stateDir, home);
        if (roots.length === 0) return NO_ROOTS;
        return deps.runtime.runDevScan(roots, include);
      });
    },

    execute(taskId: unknown): Promise<DevScanRunResult> {
      const id = validateTaskId(taskId);
      return guarded(() => deps.runtime.executeDevScan(id));
    },

    report(taskId: unknown): Promise<DevScanRunResult> {
      return deps.runtime.devScanReport(validateTaskId(taskId));
    },
  };
}
