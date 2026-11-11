// Development HQ scan: owner-approved roots (main process only).
//
// The approved-roots file lives in the private Chief state directory. Only this module writes it,
// and only after the owner picks a folder in a native dialog. cosd re-validates every root at scan
// time (cosd/execution/dev_hq_scan.py), so this module is a convenience and a second fence, not
// the only authority. The renderer never supplies a path to scan.
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export const DEV_ROOTS_FILENAME = "dev_hq_roots.json";
export const MAX_APPROVED_ROOTS = 16;
const MAX_ROOTS_FILE_BYTES = 65_536;
const MAX_PATH_LEN = 1024;

// Mirrors EXCLUDED_DIR_NAMES / _SECRET_NAME_RE in the Python scanner.
const EXCLUDED_DIR_NAMES = new Set([
  ".ssh", ".gnupg", ".aws", ".kube", ".docker", ".config", ".npm", ".claude", ".cursor", ".local",
  ".trash", "keychains", "chiefofstaff", ".git",
]);
const SECRET_NAME = /(credential|secret|keychain|passw(or)?d|(^|[._-])tokens?($|[._-])|private[._-]?keys?)/i;

export type RootCheck = { ok: true; path: string } | { ok: false; error: string };
export type RootsOptions = { home?: string; stateDir: string };

function within(child: string, parent: string): boolean {
  const rel = path.relative(parent, child);
  return rel === "" || (!rel.startsWith("..") && !path.isAbsolute(rel));
}

function realOrNull(p: string): string | null {
  try {
    return fs.realpathSync(p);
  } catch {
    return null;
  }
}

/** Canonicalise a candidate root and apply the exclusion policy. Fails closed. */
export function validateRootCandidate(candidate: unknown, opts: RootsOptions): RootCheck {
  if (typeof candidate !== "string" || candidate.length === 0 || candidate.length > MAX_PATH_LEN || candidate.includes("\0")) {
    return { ok: false, error: "root must be a folder path" };
  }
  if (!path.isAbsolute(candidate)) return { ok: false, error: "root must be an absolute path" };
  const real = realOrNull(candidate);
  if (real === null) return { ok: false, error: "folder does not exist or cannot be opened" };
  let isDir = false;
  try {
    isDir = fs.statSync(real).isDirectory();
  } catch {
    isDir = false;
  }
  if (!isDir) return { ok: false, error: "selection is not a folder" };

  const home = realOrNull(opts.home ?? os.homedir()) ?? (opts.home ?? os.homedir());
  const state = realOrNull(opts.stateDir) ?? opts.stateDir;
  if (real === path.parse(real).root) return { ok: false, error: "the whole disk cannot be approved" };
  if (real === home || within(home, real)) return { ok: false, error: "your home folder (or a parent of it) cannot be approved; pick a projects folder inside it" };
  if (within(real, path.join(home, "Library")) || within(real, path.join(home, ".Trash"))) {
    return { ok: false, error: "Library and Trash folders cannot be approved" };
  }
  if (within(real, state) || within(state, real)) return { ok: false, error: "Chief's own state folder cannot be approved" };
  for (const part of real.split(path.sep).filter(Boolean)) {
    if (EXCLUDED_DIR_NAMES.has(part.toLowerCase())) return { ok: false, error: "that folder is private or holds credentials" };
  }
  if (SECRET_NAME.test(path.basename(real))) return { ok: false, error: "that folder looks like a credential location" };
  return { ok: true, path: real };
}

function rootsFile(stateDir: string): string {
  return path.join(stateDir, DEV_ROOTS_FILENAME);
}

/** Read approved roots. A missing file means none; an unsafe file is treated as none (fail closed). */
export function readApprovedRoots(stateDir: string, opts?: { home?: string }): string[] {
  const file = rootsFile(stateDir);
  let st: fs.Stats;
  try {
    st = fs.lstatSync(file);
  } catch {
    return [];
  }
  if (!st.isFile() || st.size > MAX_ROOTS_FILE_BYTES) return [];
  if (typeof process.getuid === "function" && st.uid !== process.getuid()) return [];
  if ((st.mode & 0o022) !== 0) return [];
  let data: unknown;
  try {
    data = JSON.parse(fs.readFileSync(file, "utf-8"));
  } catch {
    return [];
  }
  const raw = typeof data === "object" && data !== null ? (data as { roots?: unknown }).roots : undefined;
  if (!Array.isArray(raw)) return [];
  const roots: string[] = [];
  for (const entry of raw.slice(0, MAX_APPROVED_ROOTS)) {
    const check = validateRootCandidate(entry, { stateDir, home: opts?.home });
    if (check.ok && !roots.includes(check.path)) roots.push(check.path);
  }
  return roots.sort();
}

function writeRoots(stateDir: string, roots: string[]): void {
  const file = rootsFile(stateDir);
  const tmp = `${file}.${process.pid}.tmp`;
  const body = JSON.stringify({ schema_version: 1, roots }, null, 2);
  const fd = fs.openSync(tmp, fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_TRUNC, 0o600);
  try {
    fs.writeSync(fd, body);
    fs.fsyncSync(fd);
  } finally {
    fs.closeSync(fd);
  }
  fs.chmodSync(tmp, 0o600);
  fs.renameSync(tmp, file); // atomic replace; never leaves a half-written approval file
}

export type RootsChange = { ok: true; roots: string[] } | { ok: false; error: string };

export function addApprovedRoot(stateDir: string, candidate: unknown, opts?: { home?: string }): RootsChange {
  const check = validateRootCandidate(candidate, { stateDir, home: opts?.home });
  if (!check.ok) return check;
  const current = readApprovedRoots(stateDir, opts);
  if (current.includes(check.path)) return { ok: true, roots: current };
  if (current.length >= MAX_APPROVED_ROOTS) return { ok: false, error: `at most ${MAX_APPROVED_ROOTS} roots can be approved` };
  // A root nested inside an already approved root adds nothing; an enclosing root replaces its children.
  if (current.some((r) => within(check.path, r))) return { ok: true, roots: current };
  const next = [...current.filter((r) => !within(r, check.path)), check.path].sort();
  try {
    writeRoots(stateDir, next);
  } catch {
    return { ok: false, error: "could not save the approved roots" };
  }
  return { ok: true, roots: next };
}

export function removeApprovedRoot(stateDir: string, rootPath: unknown, opts?: { home?: string }): RootsChange {
  if (typeof rootPath !== "string" || rootPath.length === 0 || rootPath.length > MAX_PATH_LEN) {
    return { ok: false, error: "root invalid" };
  }
  const current = readApprovedRoots(stateDir, opts);
  if (!current.includes(rootPath)) return { ok: false, error: "that folder is not an approved root" };
  const next = current.filter((r) => r !== rootPath);
  try {
    writeRoots(stateDir, next);
  } catch {
    return { ok: false, error: "could not save the approved roots" };
  }
  return { ok: true, roots: next };
}

/** The only task payload the desktop ever builds. Roots come from the approved file, never the UI. */
export function buildScanPayload(roots: string[], includeProcesses: boolean): { roots: string[]; include_processes: boolean } {
  return { roots: [...roots], include_processes: includeProcesses };
}
