"""Development HQ scan (V0): a bounded, read-only inventory of approved development roots.

Design rules (see docs/dev-hq-scan-v0.md):

* The scan only ever looks inside owner-approved roots. Approval lives in a private file in the
  Chief state directory (``dev_hq_roots.json``) that cosd never writes. A task payload may
  *narrow* the scan to sub-paths of an approved root, but it can never widen it.
* Detection is deterministic code. No model decides scope or permissions.
* Only metadata is read. File contents are never opened. Symlinks are never followed.
* Git is run with argument arrays, a minimal environment, ``GIT_OPTIONAL_LOCKS=0``, no network
  operations, and an explicit timeout. A repository's own config cannot make Git run commands
  (``core.fsmonitor`` is forced off on the command line).
* Every limit (depth, entries, repositories, time, output size) is explicit. Hitting a limit makes
  the report ``partial`` and says which limit was hit. A report is never silently truncated.
* Nothing is modified: no processes are signalled except children this module itself started.
"""
from __future__ import annotations

import json
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from cosd.tasks import MAX_JSON_BYTES

SCHEMA_VERSION = 1
SCAN_TYPE = "dev_hq_scan"
ROOTS_FILENAME = "dev_hq_roots.json"
MAX_ROOTS_FILE_BYTES = 65_536
MAX_APPROVED_ROOTS = 16
MAX_REQUESTED_ROOTS = 16
RESULT_MAX_BYTES = MAX_JSON_BYTES - 2_048  # headroom under the task-result limit
LARGE_DIR_BYTES = 100 * 1024 * 1024
STALE_AGE_S = 12 * 3600
MAX_WARNINGS = 20

PAYLOAD_KEYS = frozenset({"roots", "include_processes", "limits"})
LIMIT_KEYS = frozenset({"max_depth", "max_entries", "max_repos", "max_seconds"})

# Directory names that are never entered, whatever root they sit under.
EXCLUDED_DIR_NAMES = frozenset(
    {
        ".ssh", ".gnupg", ".aws", ".kube", ".docker", ".config", ".npm", ".claude",
        ".cursor", ".local", ".trash", "keychains", "chiefofstaff", ".git",
    }
)
# Credential-like names are skipped too (case-insensitive).
_SECRET_NAME_RE = re.compile(
    r"(credential|secret|keychain|passw(or)?d|(^|[._-])tokens?($|[._-])|private[._-]?keys?)",
    re.IGNORECASE,
)
# Derived/bulky directory names: measured (bounded), never descended into.
STORAGE_KINDS = {
    "node_modules": "node_modules",
    ".venv": "python_venv",
    "venv": "python_venv",
    "dist": "build_output",
    "build": "build_output",
    "out": "build_output",
    "target": "build_output",
    ".next": "build_output",
    ".nuxt": "build_output",
    ".turbo": "build_output",
    ".build": "build_output",
    ".gradle": "build_output",
    "deriveddata": "build_output",
    "pods": "build_output",
}
_NOISE_TOKENS = frozenset(
    {"copy", "old", "backup", "bak", "new", "final", "orig", "tmp", "temp", "archive",
     "archived", "clone", "dup", "duplicate"}
)

PROCESS_NODE_NAMES = frozenset(
    {"node", "npm", "npx", "pnpm", "yarn", "bun", "deno", "vite", "esbuild", "tsx", "jest", "vitest"}
)
PROCESS_AGENT_PREFIXES = ("claude", "codex", "cursor", "aider")


class ScanDenied(Exception):
    """The scan request is not permitted or is malformed. ``permanent`` means retrying cannot help."""

    def __init__(self, reason: str, *, permanent: bool = True):
        super().__init__(reason)
        self.reason = reason
        self.permanent = permanent


# --------------------------------------------------------------------------- limits


@dataclass(frozen=True)
class ScanLimits:
    max_depth: int = 5
    max_entries: int = 40_000
    max_repos: int = 150
    max_seconds: float = 40.0
    git_timeout_s: float = 8.0
    git_output_bytes: int = 262_144
    measure_entries_per_dir: int = 15_000
    measure_entries_total: int = 120_000
    max_output_bytes: int = RESULT_MAX_BYTES


HARD_CAPS = ScanLimits(max_depth=8, max_entries=100_000, max_repos=300, max_seconds=60.0)


def limits_from_payload(raw: Any) -> ScanLimits:
    """Payload limits may only tighten the defaults, never exceed the hard caps."""
    base = ScanLimits()
    if raw is None:
        return base
    if not isinstance(raw, dict):
        raise ScanDenied("limits must be an object")
    unknown = set(raw) - LIMIT_KEYS
    if unknown:
        raise ScanDenied("unknown limit keys")
    values: dict[str, Any] = {}
    for key in LIMIT_KEYS:
        if key not in raw:
            continue
        value = raw[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
            raise ScanDenied(f"limit {key} must be a positive number")
        cap = getattr(HARD_CAPS, key)
        value = min(value, cap)
        values[key] = float(value) if key == "max_seconds" else int(value)
    return ScanLimits(**{**base.__dict__, **values})


# --------------------------------------------------------------------------- roots


def roots_file_path(state_base: Path | None = None) -> Path:
    if state_base is None:
        from cos.config import state_dir

        state_base = state_dir()
    return Path(state_base) / ROOTS_FILENAME


def _is_within(child: Path, parent: Path) -> bool:
    return child == parent or parent in child.parents


def _real_home(home: Path | None) -> Path:
    return Path(os.path.realpath(home if home is not None else Path.home()))


def _root_denied_reason(real: Path, *, home: Path, state: Path) -> str | None:
    if real == Path(real.anchor):
        return "filesystem root is not allowed"
    if real == home or real in home.parents:
        return "home directory (or a parent of it) is not allowed"
    if _is_within(real, home / "Library") or _is_within(real, home / ".Trash"):
        return "Library and Trash are not allowed"
    if _is_within(real, state) or _is_within(state, real):
        return "Chief state directory overlap is not allowed"
    for part in real.parts[1:]:
        if part.lower() in EXCLUDED_DIR_NAMES:
            return "root is inside a private or excluded directory"
    if _SECRET_NAME_RE.search(real.name):
        return "root looks like a credential location"
    return None


def resolve_root(raw: Any, *, home: Path | None = None, state_base: Path | None = None) -> Path:
    """Canonicalise one candidate root and apply the exclusion policy (fails closed)."""
    if not isinstance(raw, str) or not raw or len(raw) > 1024 or "\x00" in raw:
        raise ScanDenied("root must be a non-empty path string")
    candidate = Path(raw)
    if not candidate.is_absolute():
        raise ScanDenied("root must be an absolute path")
    try:
        real = Path(os.path.realpath(candidate, strict=True))
    except OSError:
        raise ScanDenied("root does not exist or cannot be resolved")
    if not real.is_dir():
        raise ScanDenied("root is not a directory")
    state = Path(os.path.realpath(roots_file_path(state_base).parent))
    reason = _root_denied_reason(real, home=_real_home(home), state=state)
    if reason:
        raise ScanDenied(reason)
    return real


def _read_roots_file(path: Path) -> list[Any]:
    """Read the approval file only if it is a private regular file owned by this user."""
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return []
    except OSError:
        raise ScanDenied("approved-roots file cannot be read", permanent=False)
    if not stat.S_ISREG(st.st_mode):
        raise ScanDenied("approved-roots file is not a regular file")
    if st.st_uid != os.getuid() or st.st_mode & 0o022:
        raise ScanDenied("approved-roots file has unsafe ownership or permissions")
    if st.st_size > MAX_ROOTS_FILE_BYTES:
        raise ScanDenied("approved-roots file is too large")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ScanDenied("approved-roots file is not valid JSON")
    roots = data.get("roots") if isinstance(data, dict) else None
    if not isinstance(roots, list):
        raise ScanDenied("approved-roots file has no roots list")
    return roots[:MAX_APPROVED_ROOTS]


def load_approved_roots(
    state_base: Path | None = None, *, home: Path | None = None
) -> tuple[list[Path], list[dict[str, str]]]:
    """Return (canonical approved roots, warnings). Invalid entries are dropped with a warning."""
    entries = _read_roots_file(roots_file_path(state_base))
    roots: list[Path] = []
    warnings: list[dict[str, str]] = []
    for raw in entries:
        try:
            real = resolve_root(raw, home=home, state_base=state_base)
        except ScanDenied as exc:
            warnings.append({"code": "approved_root_invalid", "message": f"an approved root was ignored: {exc.reason}"})
            continue
        if real not in roots:
            roots.append(real)
    return sorted(roots), warnings


def select_scan_roots(
    requested: Any, approved: list[Path], *, home: Path | None = None, state_base: Path | None = None
) -> list[Path]:
    """Roots to scan. Requested roots must each lie inside an approved root."""
    if not approved:
        raise ScanDenied("no approved development roots: approve a root in Chief before scanning")
    if requested is None or requested == []:
        chosen = list(approved)
    else:
        if not isinstance(requested, list) or len(requested) > MAX_REQUESTED_ROOTS:
            raise ScanDenied("roots must be a short list of paths")
        chosen = []
        for raw in requested:
            real = resolve_root(raw, home=home, state_base=state_base)
            parent = next((root for root in approved if _is_within(real, root)), None)
            if parent is None:
                raise ScanDenied("requested root is outside the approved roots")
            # The traversal never enters excluded names, so a requested sub-root must not start inside one.
            if any(_name_excluded(part) for part in real.relative_to(parent).parts):
                raise ScanDenied("requested root is inside an excluded or credential-like folder")
            chosen.append(real)
    chosen = sorted(set(chosen))
    # Drop roots nested inside another chosen root so nothing is scanned twice.
    return [r for r in chosen if not any(o != r and _is_within(r, o) for o in chosen)]


# --------------------------------------------------------------------------- bounded subprocesses


@dataclass
class BoundedResult:
    ok: bool
    stdout: str = ""
    returncode: int | None = None
    timed_out: bool = False
    truncated: bool = False
    error: str | None = None


def _terminate(proc: subprocess.Popen) -> None:
    """Stop a child *this module started*. Only its own process group is signalled."""
    if proc.poll() is None:
        for sig, wait_s in ((signal.SIGTERM, 1.0), (signal.SIGKILL, 2.0)):
            try:
                os.killpg(proc.pid, sig)  # pgid == pid: child was started with start_new_session
            except (ProcessLookupError, PermissionError):
                break
            try:
                proc.wait(timeout=wait_s)
                break
            except subprocess.TimeoutExpired:
                continue
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:  # pragma: no cover - unkillable child
        pass
    if proc.stdout is not None:
        try:
            proc.stdout.close()
        except OSError:
            pass


def run_bounded(
    argv: list[str],
    *,
    cwd: str | None = None,
    env: dict[str, str] | None = None,
    timeout_s: float,
    max_bytes: int,
    clock: Callable[[], float] = time.monotonic,
) -> BoundedResult:
    """Run ``argv`` (never through a shell) with a wall-clock deadline and an output cap."""
    try:
        proc = subprocess.Popen(  # noqa: S603 - argument array, no shell
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            close_fds=True,
        )
    except OSError as exc:
        return BoundedResult(ok=False, error=f"spawn failed: {type(exc).__name__}")
    buf = bytearray()
    timed_out = truncated = False
    deadline = clock() + max(0.0, timeout_s)
    sel = selectors.DefaultSelector()
    try:
        sel.register(proc.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - clock()
            if remaining <= 0:
                timed_out = True
                break
            if not sel.select(min(remaining, 0.25)):
                continue
            chunk = os.read(proc.stdout.fileno(), 65_536)
            if not chunk:
                break
            room = max_bytes - len(buf)
            buf += chunk[: max(room, 0)]
            if len(chunk) > room:
                truncated = True
                break
    finally:
        sel.close()
        if timed_out or truncated:
            _terminate(proc)
        else:
            try:
                proc.wait(timeout=max(0.5, min(5.0, deadline - clock())))
            except subprocess.TimeoutExpired:
                timed_out = True
            _terminate(proc)
    text = bytes(buf).decode("utf-8", errors="replace")
    if timed_out:
        return BoundedResult(ok=False, stdout=text, timed_out=True, truncated=truncated, error="timeout")
    ok = proc.returncode == 0 or truncated
    return BoundedResult(ok=ok, stdout=text, returncode=proc.returncode, truncated=truncated,
                         error=None if ok else f"exit {proc.returncode}")


def _git_env() -> dict[str, str]:
    return {
        "PATH": "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
        "HOME": os.environ.get("HOME", ""),
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "GIT_CONFIG_NOSYSTEM": "1",
    }


GitRunner = Callable[[list[str], str, float, int], BoundedResult]


def _real_git_runner(args: list[str], cwd: str, timeout_s: float, max_bytes: int) -> BoundedResult:
    env = _git_env()
    git = shutil.which("git", path=env["PATH"])
    if git is None:
        return BoundedResult(ok=False, error="git unavailable")
    # For an ordinary repository pin the git dir and work tree to the discovered folder, so config
    # such as core.worktree or a redirected gitdir cannot point Git at a location outside the root.
    pin: list[str] = []
    gitdir = os.path.join(cwd, ".git")
    if os.path.isdir(gitdir) and not os.path.islink(gitdir):
        pin = ["--git-dir", gitdir, "--work-tree", cwd]
    argv = [git, "-c", "core.fsmonitor=false", "--no-optional-locks", *pin, "-C", cwd, *args]
    return run_bounded(argv, env=env, timeout_s=timeout_s, max_bytes=max_bytes)


# --------------------------------------------------------------------------- context


@dataclass
class ScanDeps:
    clock: Callable[[], float] = time.monotonic
    wall: Callable[[], datetime] = lambda: datetime.now(timezone.utc)
    git: GitRunner = _real_git_runner
    ps: Callable[[float], str | None] | None = None
    home: Path | None = None


class _Ctx:
    def __init__(self, limits: ScanLimits, deps: ScanDeps):
        self.limits = limits
        self.deps = deps
        self.start = deps.clock()
        self.entries = 0
        self.measure_entries = 0
        self.limits_hit: set[str] = set()
        self.warnings: list[dict[str, str]] = []
        self.counters = {
            "inaccessible_directories": 0,
            "excluded_directories_skipped": 0,
            "symlinks_skipped": 0,
            "symlinks_escaping_root": 0,
        }

    def remaining(self) -> float:
        return self.limits.max_seconds - (self.deps.clock() - self.start)

    def expired(self) -> bool:
        if self.remaining() <= 0:
            self.limits_hit.add("deadline")
            return True
        return False

    def warn(self, code: str, message: str) -> None:
        self.warnings.append({"code": code, "message": message})


def _name_excluded(name: str) -> bool:
    low = name.lower()
    return low in EXCLUDED_DIR_NAMES or bool(_SECRET_NAME_RE.search(low))


# --------------------------------------------------------------------------- filesystem walk


@dataclass
class _Candidate:
    path: Path
    git_marker: str  # "dir" | "file"


def _walk_root(root: Path, ctx: _Ctx, repos: list[_Candidate], storage: list[tuple[Path, str]]) -> None:
    limits = ctx.limits
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        if ctx.expired():
            return
        directory, depth = stack.pop()
        try:
            it = os.scandir(directory)
        except OSError:
            ctx.counters["inaccessible_directories"] += 1
            continue
        children: list[os.DirEntry] = []
        with it:
            try:
                for entry in it:
                    if ctx.entries >= limits.max_entries:
                        ctx.limits_hit.add("entry_limit")
                        break
                    ctx.entries += 1
                    children.append(entry)
            except OSError:
                ctx.counters["inaccessible_directories"] += 1
        children.sort(key=lambda e: e.name)
        subdirs: list[tuple[str, Path]] = []
        for entry in children:
            name = entry.name
            try:
                is_link = entry.is_symlink()
                is_dir = (not is_link) and entry.is_dir(follow_symlinks=False)
                is_file = (not is_link) and entry.is_file(follow_symlinks=False)
            except OSError:
                ctx.counters["inaccessible_directories"] += 1
                continue
            if is_link:
                ctx.counters["symlinks_skipped"] += 1
                try:
                    target = Path(os.path.realpath(entry.path))
                    if not _is_within(target, root):
                        ctx.counters["symlinks_escaping_root"] += 1
                except OSError:
                    pass
                continue
            if name == ".git":
                if is_dir or is_file:  # a .git file marks a linked worktree or submodule
                    if len(repos) < limits.max_repos:
                        repos.append(_Candidate(directory, "dir" if is_dir else "file"))
                    else:
                        ctx.limits_hit.add("repo_limit")
                continue
            if not is_dir:
                continue  # files are never opened; only their type is known
            if _name_excluded(name):
                ctx.counters["excluded_directories_skipped"] += 1
                continue
            kind = STORAGE_KINDS.get(name.lower())
            if kind:
                storage.append((directory / name, kind))
                continue
            subdirs.append((name, directory / name))
        for _, child in reversed(subdirs):  # reversed so the stack pops in sorted order
            if depth + 1 > limits.max_depth:
                ctx.limits_hit.add("depth_limit")
                break
            stack.append((child, depth + 1))


# --------------------------------------------------------------------------- storage measurement


def measure_dir(path: Path, ctx: _Ctx) -> tuple[int | None, str]:
    """Allocated bytes under ``path`` without following symlinks or reading contents.

    Returns (bytes, measurement) where measurement is ``exact`` (fully walked), ``partial``
    (a limit was hit; bytes is a lower bound) or ``unavailable``.
    """
    total = 0
    visited = 0
    stack = [path]
    is_top = True
    while stack:
        if ctx.expired():
            return total, "partial"
        if ctx.measure_entries >= ctx.limits.measure_entries_total:
            ctx.limits_hit.add("measure_budget")
            return total, "partial"
        current = stack.pop()
        try:
            it = os.scandir(current)
        except OSError:
            if is_top:
                return None, "unavailable"
            ctx.counters["inaccessible_directories"] += 1
            continue
        is_top = False
        with it:
            try:
                for entry in it:
                    if visited >= ctx.limits.measure_entries_per_dir:
                        return total, "partial"
                    if ctx.measure_entries >= ctx.limits.measure_entries_total:
                        ctx.limits_hit.add("measure_budget")
                        return total, "partial"
                    visited += 1
                    ctx.measure_entries += 1
                    try:
                        if entry.is_symlink():
                            continue
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                            continue
                        st = entry.stat(follow_symlinks=False)
                        total += getattr(st, "st_blocks", 0) * 512 or st.st_size
                    except OSError:
                        continue
            except OSError:
                ctx.counters["inaccessible_directories"] += 1
    return total, "exact"


# --------------------------------------------------------------------------- git inspection


def _parse_status(text: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "branch": None, "detached": False, "head": None, "unborn": False,
        "has_upstream": False, "ahead": None, "behind": None,
        "modified_count": 0, "untracked_count": 0,
    }
    for line in text.splitlines():
        if line.startswith("# branch.oid "):
            oid = line[len("# branch.oid "):].strip()
            if oid == "(initial)":
                info["unborn"] = True
            elif re.fullmatch(r"[0-9a-f]{40,64}", oid):
                info["head"] = oid[:7]
        elif line.startswith("# branch.head "):
            head = line[len("# branch.head "):].strip()
            if head == "(detached)":
                info["detached"] = True
            else:
                info["branch"] = head[:120]
        elif line.startswith("# branch.upstream "):
            info["has_upstream"] = True
        elif line.startswith("# branch.ab "):
            m = re.fullmatch(r"# branch\.ab \+(\d+) -(\d+)", line.strip())
            if m:
                info["ahead"], info["behind"] = int(m.group(1)), int(m.group(2))
        elif line.startswith(("1 ", "2 ", "u ")):
            info["modified_count"] += 1
        elif line.startswith("? "):
            info["untracked_count"] += 1
    return info


def _inspect_repo(cand: _Candidate, ctx: _Ctx) -> dict[str, Any]:
    limits = ctx.limits
    repo: dict[str, Any] = {
        "path": str(cand.path),
        "name": cand.path.name[:120],
        "linked_worktree_or_submodule": cand.git_marker == "file",
    }
    errors: list[str] = []
    cwd = str(cand.path)
    if ctx.expired():
        repo["errors"] = ["skipped: scan deadline reached"]
        return repo
    timeout = max(0.1, min(limits.git_timeout_s, ctx.remaining()))
    res = ctx.deps.git(
        ["status", "--porcelain=v2", "--branch", "--untracked-files=normal", "--no-renames"],
        cwd, timeout, limits.git_output_bytes,
    )
    if res.timed_out:
        errors.append("git status timed out")
        ctx.limits_hit.add("git_timeout")
    elif not res.ok:
        errors.append(f"git status failed: {res.error or 'unknown'}")
    else:
        info = _parse_status(res.stdout)
        repo.update(
            branch=info["branch"], detached=info["detached"], head=info["head"], unborn=info["unborn"],
            dirty=info["modified_count"] + info["untracked_count"] > 0,
            modified_count=info["modified_count"], untracked_count=info["untracked_count"],
            has_upstream=info["has_upstream"], ahead=info["ahead"], behind=info["behind"],
            ahead_behind="known" if info["ahead"] is not None else "unknown",
        )
        if res.truncated:
            repo["counts_truncated"] = True
            errors.append("git status output exceeded cap: counts are lower bounds")
            ctx.limits_hit.add("git_output_cap")
    if not ctx.expired():
        timeout = max(0.1, min(limits.git_timeout_s, ctx.remaining()))
        wt = ctx.deps.git(["worktree", "list", "--porcelain"], cwd, timeout, 65_536)
        if wt.ok and not wt.timed_out:
            repo["worktree_count"] = sum(1 for ln in wt.stdout.splitlines() if ln.startswith("worktree "))
        else:
            errors.append("worktree count unavailable")
    if cand.git_marker == "dir" and not ctx.expired():
        size, how = measure_dir(cand.path / ".git", ctx)
        repo["git_dir_size"] = {"bytes": size, "measurement": "bounded_estimate" if how == "exact" else how}
    if errors:
        repo["errors"] = errors
    return repo


# --------------------------------------------------------------------------- duplicates


def normalize_name(name: str) -> str:
    lowered = re.sub(r"\(\d+\)", " ", name.lower())
    tokens = [t for t in re.split(r"[^a-z0-9]+", lowered) if t]
    kept = [t for t in tokens if t not in _NOISE_TOKENS and not re.fullmatch(r"v?\d{1,2}", t)]
    return "-".join(kept) or "-".join(tokens) or lowered


def _root_commits(path: str, ctx: _Ctx) -> set[str] | None:
    if ctx.expired():
        return None
    res = ctx.deps.git(
        ["rev-list", "--max-parents=0", "HEAD"], path,
        max(0.1, min(5.0, ctx.remaining())), 4_096,
    )
    if not res.ok or res.timed_out:
        return None
    return {ln.strip() for ln in res.stdout.splitlines() if re.fullmatch(r"[0-9a-f]{40,64}", ln.strip())} or None


def find_duplicate_families(repos: list[dict[str, Any]], ctx: _Ctx) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for repo in repos:
        if repo.get("linked_worktree_or_submodule"):
            continue  # a linked worktree is not a duplicate of its parent
        groups.setdefault(normalize_name(repo["name"]), []).append(repo)
    families: list[dict[str, Any]] = []
    for key in sorted(groups):
        members = groups[key]
        if len(members) < 2:
            continue
        members = sorted(members, key=lambda r: r["path"])[:6]
        evidence = ["similar_name"]
        commits = [_root_commits(m["path"], ctx) for m in members]
        if all(c is not None for c in commits):
            counts: dict[str, int] = {}
            for c in commits:
                for oid in c:  # type: ignore[union-attr]
                    counts[oid] = counts.get(oid, 0) + 1
            if any(n >= 2 for n in counts.values()):
                evidence.append("shared_root_commit")
                if any(all(counts[o] < 2 for o in c) for c in commits):  # type: ignore[union-attr]
                    evidence.append("includes_unrelated_history")
            else:
                evidence.append("different_root_commits")
        else:
            evidence.append("root_commit_unavailable")
        families.append(
            {
                "classification": "possible_duplicate_family",
                "normalized_name": key[:120],
                "members": [{"name": m["name"], "path": m["path"]} for m in members],
                "evidence": evidence,
                "requires_owner_review": True,
            }
        )
        if len(families) >= 10:
            ctx.limits_hit.add("duplicate_family_limit")
            break
    return families


# --------------------------------------------------------------------------- processes


def _real_ps(timeout_s: float) -> str | None:
    res = run_bounded(
        ["/bin/ps", "-axo", "pid=,ppid=,rss=,etime=,comm="],
        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        timeout_s=timeout_s, max_bytes=2_000_000,
    )
    return res.stdout if res.ok and not res.timed_out else None


def _etime_seconds(text: str) -> int | None:
    m = re.fullmatch(r"(?:(?:(\d+)-)?(\d+):)?(\d+):(\d+)", text.strip())
    if not m:
        return None
    days, hours, minutes, seconds = (int(g) if g else 0 for g in m.groups())
    return ((days * 24 + hours) * 60 + minutes) * 60 + seconds


def categorize_process(name: str) -> str | None:
    low = name.lower()
    if low.startswith("ollama"):
        return "ollama"
    if "simulator" in low or low in ("simctl", "launchd_sim"):
        return "simulator"
    if low.startswith(PROCESS_AGENT_PREFIXES):
        return "coding_agent"
    if low in PROCESS_NODE_NAMES:
        return "node_js"
    if low.startswith("python"):
        return "python"
    return None


def collect_processes(ctx: _Ctx, *, top_n: int = 10) -> list[dict[str, Any]]:
    """Metadata-only process overview. Never reads command-line arguments or environment."""
    ps = ctx.deps.ps or _real_ps
    text = ps(min(5.0, max(0.5, ctx.remaining())))
    if text is None:
        ctx.warn("process_snapshot_unavailable", "process snapshot could not be collected; scan continues")
        return []
    collected_at = ctx.deps.wall().isoformat(timespec="seconds")
    own = {os.getpid(), os.getppid()}
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        try:
            pid, ppid, rss_kb = int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            continue
        name = os.path.basename(parts[4].strip())[:40]
        category = categorize_process(name)
        if category is None:
            continue
        rows.append(
            {
                "pid": pid, "name": name, "category": category, "rss_bytes": rss_kb * 1024,
                "collected_at": collected_at, "_ppid": ppid, "_age": _etime_seconds(parts[3]),
            }
        )
    rows.sort(key=lambda r: (-r["rss_bytes"], r["pid"]))
    findings: list[dict[str, Any]] = []
    for r in rows[:top_n]:
        findings.append({"finding": "process_memory", **{k: v for k, v in r.items() if not k.startswith("_")}})
    stale = [
        r for r in rows
        if r["category"] in ("node_js", "python") and r["_ppid"] == 1
        and (r["_age"] or 0) >= STALE_AGE_S and r["pid"] not in own
    ]
    for r in stale[:5]:
        findings.append(
            {
                "finding": "possible_stale_process",
                **{k: v for k, v in r.items() if not k.startswith("_")},
                "evidence": ["parent_is_launchd", "running_over_12h"],
                "requires_owner_review": True,
            }
        )
    return findings


# --------------------------------------------------------------------------- report


def _partial_recommendation() -> dict[str, str]:
    return {
        "code": "scan_was_partial", "severity": "info",
        "message": "This scan hit a limit or could not read some locations, so results are incomplete. "
                   "Narrow the approved roots or re-run to confirm.",
    }


def _recommendations(summary: dict[str, int], process_findings: list[dict[str, Any]], status: str) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    if summary["dirty_repositories"]:
        recs.append({
            "code": "review_dirty_repositories", "severity": "attention",
            "message": f"{summary['dirty_repositories']} repositories have uncommitted or untracked changes. "
                       "Review each one before archiving, moving, or cleaning it. Chief changed nothing.",
        })
    if summary["possible_duplicate_families"]:
        recs.append({
            "code": "review_possible_duplicates", "severity": "attention",
            "message": f"{summary['possible_duplicate_families']} groups of similarly named repositories may be "
                       "duplicates. Compare them yourself; names alone are not proof.",
        })
    if summary["large_build_directories"]:
        recs.append({
            "code": "review_large_build_directories", "severity": "info",
            "message": f"{summary['large_build_directories']} build or dependency folders are over 100 MB. "
                       "They can usually be regenerated, but confirm before removing anything.",
        })
    if any(f.get("finding") == "possible_stale_process" for f in process_findings):
        recs.append({
            "code": "review_possible_stale_processes", "severity": "info",
            "message": "Some long-running background processes may be left over from earlier sessions. "
                       "Check them in Activity Monitor before deciding. Chief did not stop anything.",
        })
    if status == "partial":
        recs.append(_partial_recommendation())
    if not recs:
        recs.append({"code": "nothing_to_review", "severity": "info", "message": "No issues were found in the scanned roots."})
    return recs


def _fit_to_size(result: dict[str, Any], max_bytes: int) -> dict[str, Any]:
    """Trim list sections (never silently) until the serialised report fits."""
    def size() -> int:
        return len(json.dumps(result, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8"))

    omitted = result.setdefault("omitted", {})
    lists = ("process_findings", "storage_findings", "duplicate_families", "repositories")
    target_bytes = max_bytes - 600  # headroom for a late "partial" recommendation
    guard = 0
    while size() > target_bytes and guard < 2_000:
        guard += 1
        target = max(
            (k for k in lists if result.get(k)),
            key=lambda k: len(json.dumps(result[k], separators=(",", ":"))),
            default=None,
        )
        if target is None:
            break
        drop = max(1, len(result[target]) // 10)
        del result[target][-drop:]
        omitted[target] = omitted.get(target, 0) + drop
    if omitted:
        result["truncated"] = True
        result["status"] = "partial"
        if "output_truncated" not in result["limits_hit"]:
            result["limits_hit"] = sorted(set(result["limits_hit"]) | {"output_truncated"})
    if not omitted:
        del result["omitted"]
    if size() > max_bytes:
        raise ScanDenied("scan report cannot be made to fit the task-result limit", permanent=False)
    return result


def run_dev_hq_scan(
    payload: dict[str, Any] | None,
    *,
    state_base: Path | None = None,
    deps: ScanDeps | None = None,
) -> dict[str, Any]:
    deps = deps or ScanDeps()
    payload = payload if payload is not None else {}
    if not isinstance(payload, dict):
        raise ScanDenied("payload must be an object")
    unknown = set(payload) - PAYLOAD_KEYS
    if unknown:
        raise ScanDenied("payload has unsupported keys")
    include_processes = payload.get("include_processes", False)
    if not isinstance(include_processes, bool):
        raise ScanDenied("include_processes must be true or false")
    limits = limits_from_payload(payload.get("limits"))

    approved, approval_warnings = load_approved_roots(state_base, home=deps.home)
    roots = select_scan_roots(payload.get("roots"), approved, home=deps.home, state_base=state_base)
    if not roots:
        raise ScanDenied("no approved development roots: approve a root in Chief before scanning")

    started_at = deps.wall().isoformat(timespec="seconds")
    ctx = _Ctx(limits, deps)
    ctx.warnings.extend(approval_warnings)

    candidates: list[_Candidate] = []
    storage_dirs: list[tuple[Path, str]] = []
    for root in roots:
        if ctx.expired():
            break
        _walk_root(root, ctx, candidates, storage_dirs)

    repos = [_inspect_repo(c, ctx) for c in candidates]
    git_errors = sum(1 for r in repos if r.get("errors"))
    if git_errors:
        ctx.warn("repository_metadata_incomplete", f"{git_errors} repositories had incomplete Git metadata")

    storage: list[dict[str, Any]] = []
    for path, kind in storage_dirs:
        if ctx.expired():
            break
        size, how = measure_dir(path, ctx)
        storage.append({"path": str(path), "kind": kind, "bytes": size, "measurement": how})
    unmeasured = len(storage_dirs) - len(storage)
    if unmeasured:
        ctx.warn("storage_unmeasured", f"{unmeasured} build/dependency folders were not measured (deadline)")
    storage.sort(key=lambda s: (-(s["bytes"] or 0), s["path"]))

    families = find_duplicate_families(repos, ctx)
    process_findings = collect_processes(ctx) if include_processes else []

    repos.sort(key=lambda r: (not r.get("dirty", False), r["path"]))
    large = sum(1 for s in storage if (s["bytes"] or 0) >= LARGE_DIR_BYTES)
    summary = {
        "repositories": len(repos),
        "dirty_repositories": sum(1 for r in repos if r.get("dirty")),
        "possible_duplicate_families": len(families),
        "large_build_directories": large,
        "build_or_dependency_directories": len(storage),
        "warnings": 0,
        "possible_stale_processes": sum(1 for f in process_findings if f.get("finding") == "possible_stale_process"),
    }

    counters = ctx.counters
    status = "partial" if (ctx.limits_hit or git_errors or counters["inaccessible_directories"]) else "complete"

    warnings = ctx.warnings[:MAX_WARNINGS]
    summary["warnings"] = len(ctx.warnings)
    result: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "scan_type": SCAN_TYPE,
        "started_at": started_at,
        "finished_at": deps.wall().isoformat(timespec="seconds"),
        "status": status,
        "truncated": False,
        "roots_scanned": len(roots),
        "roots": [str(r) for r in roots],
        "include_processes": include_processes,
        "limits": {
            "max_depth": limits.max_depth, "max_entries": limits.max_entries, "max_repos": limits.max_repos,
            "max_seconds": limits.max_seconds, "max_output_bytes": limits.max_output_bytes,
        },
        "limits_hit": sorted(ctx.limits_hit),
        "coverage": {"entries_visited": ctx.entries, **counters},
        "summary": summary,
        "repositories": repos,
        "storage_findings": storage[:25],
        "duplicate_families": families,
        "process_findings": process_findings,
        "warnings": warnings,
        "recommendations": [],
    }
    if len(storage) > 25:
        result.setdefault("omitted", {})["storage_findings"] = len(storage) - 25
        result["truncated"] = True
        result["status"] = "partial"
        result["limits_hit"] = sorted(set(result["limits_hit"]) | {"output_truncated"})
    if len(ctx.warnings) > MAX_WARNINGS:
        result.setdefault("omitted", {})["warnings"] = len(ctx.warnings) - MAX_WARNINGS
    result["recommendations"] = _recommendations(summary, process_findings, result["status"])
    result = _fit_to_size(result, limits.max_output_bytes)
    if result["status"] == "partial" and not any(r["code"] == "scan_was_partial" for r in result["recommendations"]):
        result["recommendations"] = [r for r in result["recommendations"] if r["code"] != "nothing_to_review"]
        result["recommendations"].append(_partial_recommendation())
    if size_of(result) > limits.max_output_bytes:
        raise ScanDenied("scan report cannot be made to fit the task-result limit", permanent=False)
    return result


def size_of(obj: Any) -> int:
    return len(json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False).encode("utf-8"))
