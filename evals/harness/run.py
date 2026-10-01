#!/usr/bin/env python3.12
"""Chief certification harness runner (E1 Part 1: core + CLI). Stdlib only.

  python3.12 evals/harness/run.py --model fake                    # everything, fast
  python3.12 evals/harness/run.py --model real --repeat-fast-path 300 --long-session 500
  python3.12 evals/harness/run.py --suite injection --model real

Every case gets a fresh temporary COS_STATE_DIR and runs the real cos in
fixture mode (COS_FIXTURE_DIR), so nothing reads or writes Owen's real
calendar, reminders, state directory, or audit log. --model real uses bin/cos
with local Ollama; --model fake runs the same cos code with the scripted fake
model (fake_cos.py). Results go to evals/results/<run-id>/, the report to
evals/reports/<run-id>/ (both gitignored). See evals/README.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

HARNESS = Path(__file__).resolve().parent
EVALS = HARNESS.parent
REPO_ROOT = EVALS.parent
sys.path.insert(0, str(HARNESS))
sys.path.insert(1, str(REPO_ROOT))

import checks  # noqa: E402
import judge as judge_mod  # noqa: E402
import report  # noqa: E402
from cos.audit import verify  # noqa: E402  (read-only helpers from the real cos)
from cos.sessions import read_session  # noqa: E402

SUITES_DIR = EVALS / "suites"
FIXTURES_DIR = EVALS / "fixtures"
REAL_STATE_DIR = Path.home() / "Library" / "Application Support" / "ChiefOfStaff"
OLLAMA = "http://127.0.0.1:11434"
TIMEOUT_S = {"fake": 60, "real": 900}
LONG_SESSION_PROMPTS = ("what's on my calendar today", "and tomorrow?", "what time is it",
                        "anything due on my reminders?", "how's the weather looking for recess")
HARNESS_TZ = "America/New_York"


# ----------------------------------------------------------------------------- helpers

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def git_sha() -> str:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], capture_output=True,
                             text=True, timeout=10, check=False, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
        sha = out.stdout.strip()
        dirty = subprocess.run(["git", "-C", str(REPO_ROOT), "status", "--porcelain", "--", "cos", "bin"],
                               capture_output=True, text=True, timeout=10, check=False,
                               env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.strip()
        return sha + ("-dirty" if dirty else "") if sha else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


def real_state_fingerprint() -> dict:
    """Metadata only (names, sizes, mtimes); file contents are never read."""
    path = REAL_STATE_DIR
    try:
        st = path.stat()
    except FileNotFoundError:
        return {"exists": False}
    except OSError as e:
        return {"exists": None, "error": type(e).__name__}
    entries = {}
    try:
        for root, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                p = Path(root) / name
                try:
                    s = p.lstat()
                except OSError:
                    continue
                entries[str(p.relative_to(path))] = [s.st_size, s.st_mtime_ns]
    except OSError as e:
        return {"exists": True, "error": type(e).__name__}
    return {"exists": True, "mtime_ns": st.st_mtime_ns, "entries": entries}


def fingerprint_diff(before: dict, after: dict) -> list[str]:
    if before == after:
        return []
    if before.get("exists") != after.get("exists"):
        return [f"existence changed: {before.get('exists')} -> {after.get('exists')}"]
    out = []
    if before.get("mtime_ns") != after.get("mtime_ns"):
        out.append("directory mtime changed")
    b, a = before.get("entries", {}), after.get("entries", {})
    out += [f"added {k}" for k in sorted(set(a) - set(b))]
    out += [f"removed {k}" for k in sorted(set(b) - set(a))]
    out += [f"changed {k}" for k in sorted(set(a) & set(b)) if a[k] != b[k]]
    return out or ["fingerprint changed"]


def percentiles(values) -> dict:
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    if not vals:
        return {"n": 0}

    def pct(p):  # nearest-rank
        return vals[max(0, min(len(vals) - 1, math.ceil(p / 100 * len(vals)) - 1))]
    return {"n": len(vals), "min": vals[0], "p50": pct(50), "p95": pct(95), "p99": pct(99),
            "max": vals[-1], "mean": round(sum(vals) / len(vals), 1)}


# ----------------------------------------------------------------------------- cases

def load_cases(suites: list[str] | None, ids: set[str] | None) -> list[dict]:
    cases = []
    for path in sorted(SUITES_DIR.glob("*.jsonl")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("//"):
                continue
            try:
                case = json.loads(line)
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path.name}:{lineno}: invalid JSON ({e})")
            case.setdefault("suite", path.stem)
            case["_source"] = f"{path.name}:{lineno}"
            cases.append(case)
    seen = set()
    for c in cases:
        if c["id"] in seen:
            raise SystemExit(f"duplicate case id {c['id']}")
        seen.add(c["id"])
    if suites:
        cases = [c for c in cases if c["suite"] in suites]
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    return cases


def build_prompt(p) -> str:
    if isinstance(p, dict):
        unit, chars = str(p.get("repeat", "x")), int(p.get("chars", 0))
        body = (unit * (chars // max(1, len(unit)) + 1))[:max(0, chars - len(p.get("prefix", "")))]
        return str(p.get("prefix", "")) + body
    return "" if p is None else str(p)


def case_steps(case: dict) -> list[dict]:
    steps = [{"command": c, "_setup": True, "expect": {"exit_code": 0}}
             if isinstance(c, str) else {**c, "_setup": True} for c in case.get("setup") or []]
    if "turns" in case:
        steps += [dict(t) for t in case["turns"]]
    else:
        steps.append({k: case[k] for k in ("command", "prompt", "expect", "session", "json") if k in case})
    return steps


# ----------------------------------------------------------------------------- state

def session_file(state: Path, sid: str) -> Path:
    return state / "sessions" / f"{sid}.jsonl"


def synthetic_turn(i: int, answer_chars: int = 0) -> dict:
    return {"ts": f"2026-09-30T08:{i % 60:02d}:00-04:00", "question": f"Test question {i}",
            "answer": f"Test answer {i}" + ("y" * answer_chars), "tools_used": [], "fast_path": False,
            "model": "fake-scripted", "notices": [], "total_ms": 5}


def apply_mutation(state: Path, mutation: dict | None) -> None:
    """Prepare (usually corrupt) state before a case. Synthetic content only."""
    if not mutation:
        return
    if "config_raw" in mutation:
        (state / "config.json").write_text(mutation["config_raw"], encoding="utf-8")
    sid = mutation.get("session")
    if not sid:
        return
    sdir = state / "sessions"
    sdir.mkdir(mode=0o700, exist_ok=True)
    path = sdir / f"{sid}.jsonl"
    kind = mutation.get("kind", "file")
    if kind == "directory":
        path.mkdir(mode=0o700)
        return
    if kind == "symlink":
        target = state / "symlink-target.jsonl"
        target.write_text(json.dumps(synthetic_turn(0)) + "\n", encoding="utf-8")
        path.symlink_to(target)
        return
    chunks: list[bytes] = []
    for item in mutation.get("lines", []):
        if isinstance(item, str):
            chunks.append(item.encode("utf-8") + b"\n")
        elif "valid_turns" in item:
            for i in range(int(item["valid_turns"])):
                chunks.append(json.dumps(synthetic_turn(i, item.get("answer_chars", 0))).encode() + b"\n")
        elif "raw_json" in item:
            chunks.append(json.dumps(item["raw_json"]).encode() + b"\n")
        elif "giant_chars" in item:
            chunks.append(b'{"ts": "' + b"x" * int(item["giant_chars"]) + b'"}\n')
        elif "bytes_hex" in item:
            chunks.append(bytes.fromhex(item["bytes_hex"]) + b"\n")
        elif "no_newline" in item:
            chunks.append(item["no_newline"].encode("utf-8"))
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as fh:
        fh.write(b"".join(chunks))


def count_lines(path: Path) -> int | None:
    try:
        if path.is_symlink() or path.is_dir():
            return None
        with open(path, "rb") as fh:
            return sum(1 for line in fh if line.strip())
    except FileNotFoundError:
        return 0
    except OSError:
        return None


class AuditTail:
    """Reads audit records appended since the last call (by byte offset)."""

    def __init__(self, path: Path):
        self.path, self.offset = path, 0

    def new_records(self) -> list[dict]:
        try:
            with open(self.path, "rb") as fh:
                fh.seek(self.offset)
                data = fh.read()
        except FileNotFoundError:
            return []
        end = data.rfind(b"\n") + 1
        self.offset += end
        out = []
        for raw in data[:end].splitlines():
            try:
                out.append(json.loads(raw))
            except ValueError:
                out.append({"kind": "_unparseable"})
        return out


# ----------------------------------------------------------------------------- running cos

class CosRunner:
    def __init__(self, mode: str, model_name: str | None):
        self.mode, self.model_name = mode, model_name
        self.timeout = TIMEOUT_S[mode]

    def argv(self, mode: str | None = None) -> list[str]:
        if (mode or self.mode) == "fake":
            return [sys.executable, "-s", "-E", "-P", str(HARNESS / "fake_cos.py")]
        return [str(REPO_ROOT / "bin" / "cos")]

    def env(self, state: Path, fixtures: Path) -> dict:
        return {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
                "HOME": str(Path.home()), "LANG": "en_US.UTF-8", "TZ": HARNESS_TZ,
                "COS_STATE_DIR": str(state), "COS_FIXTURE_DIR": str(fixtures)}

    def prepare_state(self, state: Path, mode: str | None = None) -> None:
        state.mkdir(mode=0o700, parents=True, exist_ok=True)
        if (mode or self.mode) == "fake":
            cfg = {"model": "fake-scripted", "fallback_model": None}
        else:
            cfg = {"model": self.model_name} if self.model_name else {}
        if cfg:
            (state / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    def call(self, args: list[str], state: Path, fixtures: Path, mode: str | None = None) -> dict:
        started = time.monotonic()
        try:
            proc = subprocess.run(self.argv(mode) + args, capture_output=True, text=True,
                                  timeout=self.timeout, env=self.env(state, fixtures),
                                  stdin=subprocess.DEVNULL, cwd=str(state.parent), check=False)
            code, out, err, timed_out = proc.returncode, proc.stdout, proc.stderr, False
        except subprocess.TimeoutExpired as e:
            code, timed_out = None, True
            out = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            err = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return {"exit_code": code, "stdout": out, "stderr": err, "timed_out": timed_out,
                "wall_ms": int((time.monotonic() - started) * 1000)}


def cos_args(step: dict, prompt: str) -> list[str]:
    cmd = step.get("command", "ask")
    sid = step.get("session")
    as_json = step.get("json", True)
    if cmd == "ask":
        args = ["ask"]
        if sid is not None:
            args += ["--session", sid]
        return args + (["--json"] if as_json else []) + ["--", prompt]
    if cmd == "history":
        return ["history", "--session", sid or "default", "--json"]
    if cmd in ("brief", "status"):
        return [cmd] + (["--json"] if as_json else [])
    if cmd == "stop":
        return ["stop", "harness"]
    if cmd in ("resume", "tools"):
        return [cmd]
    if cmd == "audit_verify":
        return ["audit", "verify"]
    raise SystemExit(f"unknown command {cmd!r}")


def parse_output(cmd: str, res: dict) -> dict:
    obs = {"answer": "", "tools_used": [], "fast_path": None, "model": None, "notices": [],
           "total_ms": None, "error_kind": None, "json": None}
    stdout = res["stdout"].strip()
    data = None
    if stdout.startswith(("{", "[")):
        try:
            data = json.loads(stdout.splitlines()[-1] if cmd != "history" else stdout)
        except ValueError:
            data = None
    obs["json"] = data if isinstance(data, dict) else None
    if isinstance(data, dict):
        obs["error_kind"] = data.get("error_kind")
        if cmd == "ask" and data.get("ok"):
            for k in ("answer", "tools_used", "fast_path", "model", "notices", "total_ms"):
                obs[k] = data.get(k, obs[k])
        elif cmd == "brief" and data.get("ok"):
            obs["answer"] = "\n".join(data.get("lines") or [])
    elif cmd == "ask" and res["exit_code"] == 0 and stdout:
        obs["answer"] = stdout  # text mode
    elif cmd == "brief" and res["exit_code"] == 0:
        obs["answer"] = stdout
    return obs


def history_snapshot(runner: CosRunner, state: Path, fixtures: Path, sid: str) -> dict:
    res = runner.call(["history", "--session", sid, "--json"], state, fixtures)
    turns, skipped = None, None
    try:
        turns = len(json.loads(res["stdout"]))
    except (ValueError, TypeError):
        pass
    for line in reversed(res["stderr"].splitlines()):
        try:
            skipped = json.loads(line).get("skipped_lines")
            break
        except (ValueError, AttributeError):
            continue
    return {"exit_code": res["exit_code"], "turns": turns, "skipped": skipped, "wall_ms": res["wall_ms"]}


# ----------------------------------------------------------------------------- one case

def run_case(case: dict, runner: CosRunner, ctx: dict, judge, tmp_root: Path) -> list[dict]:
    fixtures = FIXTURES_DIR / case.get("fixtures", "default")
    state = Path(tempfile.mkdtemp(prefix=f"{case['id'][:30]}-", dir=tmp_root)) / "state"
    runner.prepare_state(state)
    apply_mutation(state, case.get("state_mutation"))
    tail = AuditTail(state / "audit.jsonl")
    case_session = case.get("session")
    kill_switch = False
    records = []
    for idx, step in enumerate(case_steps(case)):
        step.setdefault("session", case_session)
        cmd = step.get("command", "ask")
        prompt = build_prompt(step.get("prompt"))
        sid = step.get("session")
        sfile = session_file(state, sid) if sid and _valid_sid(sid) else None
        before = count_lines(sfile) if sfile else None
        res = runner.call(cos_args(step, prompt), state, fixtures)
        obs = {"command": cmd, "prompt": prompt, **res, **parse_output(cmd, res)}
        obs["audit"] = tail.new_records()
        obs["session_lines_before"], obs["session_lines_after"] = before, (count_lines(sfile) if sfile else None)
        obs["kill_switch_set"] = kill_switch
        expect = step.get("expect") or {}
        obs["history"] = (history_snapshot(runner, state, fixtures, sid)
                          if sid and _valid_sid(sid) and ("history_turns" in expect or "history_skipped" in expect)
                          else None)
        vr = verify(state / "audit.jsonl")
        obs["chain_status"], obs["chain_message"] = vr.status, vr.message
        if cmd == "stop" and res["exit_code"] == 0:
            kill_switch = True
        if cmd == "resume" and res["exit_code"] == 0:
            kill_switch = False
        results = checks.check_turn(expect, obs, ctx)
        record = {
            "case_id": case["id"], "suite": case["suite"], "turn": idx, "setup": bool(step.get("_setup")),
            "command": cmd, "prompt": prompt[:2000], "prompt_chars": len(prompt), "session": sid,
            "fixtures": case.get("fixtures", "default"), "model_mode": runner.mode,
            "answer": obs["answer"], "tools_used": obs["tools_used"], "fast_path": obs["fast_path"],
            "model": obs["model"], "notices": obs["notices"], "exit_code": obs["exit_code"],
            "error_kind": obs["error_kind"], "total_ms": obs["total_ms"], "wall_ms": obs["wall_ms"],
            "model_calls": sum(1 for r in obs["audit"] if r.get("kind") == "model_call"),
            "tool_calls": [r.get("tool") for r in obs["audit"] if r.get("kind") == "tool_call"],
            "audit_kinds": [r.get("kind") for r in obs["audit"]],
            "kill_switch_set": kill_switch if cmd in ("stop", "resume") else obs["kill_switch_set"],
            "session_lines": [before, obs["session_lines_after"]], "history": obs["history"],
            "chain": obs["chain_status"], "stderr_tail": obs["stderr"][-600:],
            "checks": results, "passed": all(c["ok"] for c in results),
        }
        if cmd not in ("ask", "brief"):
            record["output_head"] = obs["stdout"][:400]
        record["judge"] = judge.evaluate(case, record)
        records.append(record)
    if not ctx.get("keep_state"):
        shutil.rmtree(state.parent, ignore_errors=True)
    return records


def _valid_sid(sid) -> bool:
    return isinstance(sid, str) and re.fullmatch(r"[a-z0-9-]{1,40}", sid) is not None


# ----------------------------------------------------------------------------- soak runs

def run_fast_path_soak(cases, n, runner, ctx, tmp_root, out_path, log) -> dict:
    """Every single-turn case expected to take the fast path (any suite), n times, in one
    long-lived state dir. Near-miss cases are left out: they call the model."""
    soak_cases = [c for c in cases if "turns" not in c and not c.get("setup") and not c.get("state_mutation")
                  and c.get("command", "ask") == "ask" and (c.get("expect") or {}).get("fast_path") is True]
    state = Path(tempfile.mkdtemp(prefix="soak-fast-path-", dir=tmp_root)) / "state"
    runner.prepare_state(state)
    tail = AuditTail(state / "audit.jsonl")
    per_case: dict[str, dict] = {}
    totals, walls, fp_totals, fp_walls, fails = [], [], [], [], 0
    cert_violations: dict[str, int] = {}
    started = time.monotonic()
    with open(out_path, "w", encoding="utf-8") as out:
        for rep in range(n):
            for case in soak_cases:
                fixtures = FIXTURES_DIR / case.get("fixtures", "default")
                prompt = build_prompt(case.get("prompt"))
                res = runner.call(cos_args({"command": "ask"}, prompt), state, fixtures)
                obs = {"command": "ask", "prompt": prompt, **res, **parse_output("ask", res),
                       "audit": tail.new_records(), "kill_switch_set": False,
                       "session_lines_before": None, "session_lines_after": None,
                       "chain_status": "ok"}  # whole chain verified once at the end
                expect = {k: v for k, v in (case.get("expect") or {}).items()}
                results = checks.check_turn(expect, obs, ctx)
                ok = all(c["ok"] for c in results)
                fails += not ok
                for c in results:
                    if c.get("cert") and not c["ok"]:
                        cert_violations[c["cert"]] = cert_violations.get(c["cert"], 0) + 1
                key = hashlib.sha256(json.dumps([obs["answer"], obs["tools_used"], obs["fast_path"],
                                                 obs["exit_code"]]).encode()).hexdigest()[:16]
                pc = per_case.setdefault(case["id"], {"runs": 0, "fails": 0, "outcomes": {}})
                pc["runs"] += 1
                pc["fails"] += not ok
                pc["outcomes"][key] = pc["outcomes"].get(key, 0) + 1
                totals.append(obs["total_ms"])
                walls.append(res["wall_ms"])
                if obs["fast_path"]:
                    fp_totals.append(obs["total_ms"])
                    fp_walls.append(res["wall_ms"])
                out.write(json.dumps({"case_id": case["id"], "rep": rep, "exit_code": res["exit_code"],
                                      "fast_path": obs["fast_path"], "total_ms": obs["total_ms"],
                                      "wall_ms": res["wall_ms"], "passed": ok, "outcome": key,
                                      "failed_checks": [c for c in results if not c["ok"]]}) + "\n")
            log(f"soak fast_path: rep {rep + 1}/{n} done ({fails} failing runs so far)")
    vr = verify(state / "audit.jsonl")
    nondet = {cid: pc["outcomes"] for cid, pc in per_case.items() if len(pc["outcomes"]) > 1}
    if not ctx.get("keep_state"):
        shutil.rmtree(state.parent, ignore_errors=True)
    return {"repeat": n, "cases": len(soak_cases), "runs": len(walls), "failing_runs": fails,
            "seconds": round(time.monotonic() - started, 1),
            "total_ms": percentiles(totals), "wall_ms": percentiles(walls),
            "fast_path_total_ms": percentiles(fp_totals), "fast_path_wall_ms": percentiles(fp_walls),
            "nondeterministic_cases": nondet, "audit_chain": vr.status, "audit_records": vr.records,
            "per_case_fails": {cid: pc["fails"] for cid, pc in per_case.items() if pc["fails"]},
            "cert_violations": cert_violations}


def run_long_session(n, runner, ctx, tmp_root, out_path, log) -> dict:
    """One session of n turns with the fake model; samples history cost at intervals."""
    fixtures = FIXTURES_DIR / "default"
    state = Path(tempfile.mkdtemp(prefix="long-session-", dir=tmp_root)) / "state"
    runner.prepare_state(state, mode="fake")
    sid = "long-session"
    sfile = session_file(state, sid)
    tail = AuditTail(state / "audit.jsonl")
    interval = max(1, n // 25)
    samples, walls, totals, fails = [], [], [], 0
    started = time.monotonic()
    with open(out_path, "w", encoding="utf-8") as out:
        for i in range(n):
            prompt = LONG_SESSION_PROMPTS[i % len(LONG_SESSION_PROMPTS)]
            res = runner.call(cos_args({"command": "ask", "session": sid}, prompt), state, fixtures, mode="fake")
            obs = parse_output("ask", res)
            tail.new_records()
            ok = res["exit_code"] == 0 and bool(obs["answer"])
            fails += not ok
            walls.append(res["wall_ms"])
            totals.append(obs["total_ms"])
            row = {"turn": i + 1, "exit_code": res["exit_code"], "total_ms": obs["total_ms"],
                   "wall_ms": res["wall_ms"], "ok": ok}
            if (i + 1) % interval == 0 or i + 1 == n:
                t0 = time.perf_counter()
                turns, skipped = read_session(state, sid)
                load_ms = round((time.perf_counter() - t0) * 1000, 2)
                hist = history_snapshot(runner, state, fixtures, sid)
                sample = {"turn": i + 1, "file_bytes": sfile.stat().st_size, "history_load_ms": load_ms,
                          "history_turns": len(turns), "history_skipped": skipped,
                          "cos_history_wall_ms": hist["wall_ms"], "cos_history_turns": hist["turns"],
                          "ask_wall_ms": res["wall_ms"], "ask_total_ms": obs["total_ms"]}
                samples.append(sample)
                row["sample"] = sample
                log(f"long session: turn {i + 1}/{n}, file {sample['file_bytes']} bytes, "
                    f"cos history {hist['wall_ms']} ms")
            out.write(json.dumps(row) + "\n")
    final_turns, final_skipped = read_session(state, sid)
    vr = verify(state / "audit.jsonl")
    if not ctx.get("keep_state"):
        shutil.rmtree(state.parent, ignore_errors=True)
    return {"turns_requested": n, "turns_recorded": len(final_turns), "skipped_lines": final_skipped,
            "failing_turns": fails, "seconds": round(time.monotonic() - started, 1),
            "wall_ms": percentiles(walls), "total_ms": percentiles(totals), "samples": samples,
            "audit_chain": vr.status, "model_mode": "fake"}


# ----------------------------------------------------------------------------- resources

class ResourceSampler(threading.Thread):
    """Every interval seconds: memory pressure and Ollama's loaded models. No process listings."""

    def __init__(self, path: Path, interval: float):
        super().__init__(daemon=True)
        self.path, self.interval = path, interval
        self._halt = threading.Event()

    def sample(self) -> dict:
        row = {"ts": now_iso(), "t": round(time.time(), 1)}
        try:
            out = subprocess.run(["/usr/bin/memory_pressure", "-Q"], capture_output=True, text=True,
                                 timeout=15, check=False).stdout
            for line in out.splitlines():
                if "free percentage" in line:
                    row["memory_free_pct"] = int(line.rsplit(":", 1)[1].strip().rstrip("%"))
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
        if "memory_free_pct" not in row:
            try:
                out = subprocess.run(["/usr/bin/vm_stat"], capture_output=True, text=True, timeout=15,
                                     check=False).stdout
                pages = {l.split(":")[0]: int(l.split(":")[1].strip().rstrip(".")) for l in out.splitlines()[1:]
                         if ":" in l and l.split(":")[1].strip().rstrip(".").isdigit()}
                row["vm_pages_free"] = pages.get("Pages free")
            except (OSError, subprocess.SubprocessError, ValueError):
                pass
        try:
            with urllib.request.urlopen(OLLAMA + "/api/ps", timeout=3) as resp:  # local Ollama only
                models = json.loads(resp.read(1_000_000)).get("models", [])
            row["ollama_models"] = [{"name": m.get("name"), "size": m.get("size"),
                                     "size_vram": m.get("size_vram")} for m in models]
        except (OSError, ValueError):
            row["ollama_models"] = None
        return row

    def record(self) -> None:
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(self.sample()) + "\n")

    def run(self):
        while not self._halt.wait(self.interval):
            self.record()

    def stop(self):
        self._halt.set()


# ----------------------------------------------------------------------------- main

def side_effect_map(runner: CosRunner, tmp_root: Path) -> dict:
    """Tool side effects as the real cos registers them (`cos tools` in fixture mode)."""
    state = Path(tempfile.mkdtemp(prefix="tools-", dir=tmp_root)) / "state"
    runner.prepare_state(state, mode="fake")
    res = runner.call(["tools"], state, FIXTURES_DIR / "default", mode="fake")
    shutil.rmtree(state.parent, ignore_errors=True)
    out = {}
    for line in res["stdout"].splitlines():
        parts = line.split()
        if len(parts) > 1 and parts[1].startswith("side_effect="):
            out[parts[0]] = parts[1].split("=", 1)[1]
    if not out:
        raise SystemExit(f"could not read tool registry from cos tools: {res['stderr'][-400:]}")
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Chief certification harness (E1 Part 1)")
    p.add_argument("--model", choices=("fake", "real"), default="fake")
    p.add_argument("--model-name", help="real mode: Ollama model for cos (default: cos's configured default)")
    p.add_argument("--suite", action="append", help="run only this suite (repeatable)")
    p.add_argument("--case", action="append", help="run only this case id (repeatable)")
    p.add_argument("--repeat-fast-path", type=int, nargs="?", const=300, default=0, metavar="N")
    p.add_argument("--long-session", type=int, nargs="?", const=500, default=0, metavar="N")
    p.add_argument("--baseline", help="run id to compare against (default: latest with the same model mode)")
    p.add_argument("--out-root", type=Path, default=EVALS, help="parent of results/ and reports/")
    p.add_argument("--run-id")
    p.add_argument("--sample-interval", type=float, default=60.0)
    p.add_argument("--keep-state", action="store_true", help="keep temp state dirs (debugging)")
    p.add_argument("--judge", default="none")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    run_id = args.run_id or f"{datetime.now():%Y%m%d-%H%M%S}-{args.model}"
    results_dir = args.out_root / "results" / run_id
    reports_dir = args.out_root / "reports" / run_id
    results_dir.mkdir(parents=True, exist_ok=False)
    reports_dir.mkdir(parents=True, exist_ok=True)

    def log(msg):
        if not args.quiet:
            print(msg, flush=True)

    cases = load_cases(args.suite, set(args.case) if args.case else None)
    runner = CosRunner(args.model, args.model_name)
    judge = judge_mod.get_judge(args.judge)
    started_at, t0 = now_iso(), time.monotonic()
    fingerprint_before = real_state_fingerprint()
    tmp_root = Path(tempfile.mkdtemp(prefix="cos-evals-"))
    sampler = ResourceSampler(results_dir / "resources.jsonl", args.sample_interval)
    sampler.record()
    sampler.start()
    meta = {"run_id": run_id, "git_sha": git_sha(), "model_mode": args.model,
            "model_name": "fake-scripted" if args.model == "fake" else (args.model_name or "cos default"),
            "started": started_at, "suites": sorted({c["suite"] for c in cases}),
            "case_count": len(cases), "argv": sys.argv[1:] if argv is None else list(argv),
            "python": sys.version.split()[0], "tz": HARNESS_TZ}
    try:
        if args.model == "real":
            meta["model_name"] = args.model_name or _cos_default_model()
        ctx = {"side_effects": side_effect_map(runner, tmp_root), "keep_state": args.keep_state}
        meta["tools"] = ctx["side_effects"]
        with open(results_dir / "results.jsonl", "w", encoding="utf-8") as out:
            for i, case in enumerate(cases, 1):
                recs = run_case(case, runner, {**ctx, "suite": case["suite"]}, judge, tmp_root)
                for r in recs:
                    out.write(json.dumps(r, ensure_ascii=False) + "\n")
                out.flush()
                ok = all(r["passed"] for r in recs)
                ms = sum(r["wall_ms"] for r in recs)
                log(f"[{i}/{len(cases)}] {case['id']:<28} {'PASS' if ok else 'FAIL'} {ms} ms")
        soak = None
        if args.repeat_fast_path:
            soak = run_fast_path_soak(load_cases(None, None),
                                      args.repeat_fast_path, runner, ctx, tmp_root,
                                      results_dir / "soak_fast_path.jsonl", log)
        long_session = None
        if args.long_session:
            long_session = run_long_session(args.long_session, runner, ctx, tmp_root,
                                            results_dir / "long_session.jsonl", log)
    finally:
        sampler.stop()
        sampler.record()
        if not args.keep_state:
            shutil.rmtree(tmp_root, ignore_errors=True)
    fingerprint_after = real_state_fingerprint()
    meta["ended"] = now_iso()
    meta["seconds"] = round(time.monotonic() - t0, 1)
    meta["real_state_dir_changes"] = fingerprint_diff(fingerprint_before, fingerprint_after)
    meta["real_state_dir_exists"] = fingerprint_before.get("exists")
    if args.keep_state:
        meta["state_root"] = str(tmp_root)
    extras = {"soak_fast_path": soak, "long_session": long_session}
    (results_dir / "meta.json").write_text(json.dumps({**meta, **extras}, indent=2), encoding="utf-8")
    summary_path, html_path = report.build(results_dir, reports_dir, args.out_root / "reports",
                                           baseline_id=args.baseline)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    log("")
    for cert in summary["certs"]:
        log(f"{cert['id']} {cert['status']:<4} ({cert['checked']} checked) {cert['title']}")
    for suite, s in summary["suites"].items():
        log(f"  {suite:<14} {s['passed']}/{s['cases']} cases pass")
    print(f"Report: {html_path}")
    print(f"Summary: {summary_path}")
    return 0


def _cos_default_model() -> str:
    from cos.config import DEFAULTS
    return DEFAULTS["model"]


if __name__ == "__main__":
    sys.exit(main())
