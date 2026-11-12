"""Development HQ scan V0: scanner behaviour on synthetic fixtures (temp dirs only)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tests" / "cosd"))
from support import CosdStateTest  # noqa: E402

from cosd.execution import dev_hq_scan as scan  # noqa: E402
from cosd.execution.dev_hq_scan import BoundedResult, ScanDeps, ScanDenied, run_dev_hq_scan  # noqa: E402

GIT_ENV = {
    **os.environ,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid",
}


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(cwd), *args], check=True, env=GIT_ENV, capture_output=True, text=True)
    return out.stdout


def make_repo(path: Path, *, commit: bool = True, filename: str = "a.txt") -> Path:
    path.mkdir(parents=True, exist_ok=True)
    git(path, "init", "-q", "-b", "main")
    (path / filename).write_text("one\n")
    if commit:
        git(path, "add", "-A")
        git(path, "commit", "-q", "-m", "init")
    return path


def write_roots(state: Path, *roots: Path | str, mode: int = 0o600) -> Path:
    p = state / scan.ROOTS_FILENAME
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w") as fh:
        json.dump({"schema_version": 1, "roots": [str(r) for r in roots]}, fh)
    os.chmod(p, mode)
    return p


def stock_git(cwd: Path, *args: str, home: Path) -> subprocess.CompletedProcess:
    """Plain Git as a user would run it (global config visible). Used only as a canary, to prove a
    fixture really would misbehave, so a passing regression test cannot be vacuous."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG")}
    env.update(HOME=str(home), GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
    return subprocess.run(["git", "-C", str(cwd), *args], env=env, capture_output=True, text=True)


def edit_same_size(path: Path, text: str) -> None:
    """Change a tracked file without changing its size and back-date its mtime. Git compares
    timestamps at one-second granularity and hashes content (running any clean filter) only when
    the stat data differs but the size does not."""
    assert len(text) == len(path.read_text())
    path.write_text(text)
    past = time.time() - 30
    os.utime(path, (past, past))


def untracked_lines(status_output: str) -> int:
    return sum(1 for line in status_output.splitlines() if line.startswith("? "))


class StepClock:
    def __init__(self, step: float):
        self.t, self.step = 0.0, step

    def __call__(self) -> float:
        self.t += self.step
        return self.t


CLEAN_STATUS = "# branch.oid " + "a" * 40 + "\n# branch.head main\n"


def fake_git(status: str = CLEAN_STATUS, *, timed_out: bool = False, ok: bool = True,
             calls: list | None = None, pins: list | None = None):
    def runner(args, cwd, timeout, cap, git_dir=None):
        if calls is not None:
            calls.append((list(args), cwd, timeout, cap))
        if pins is not None:
            pins.append((args[0], cwd, git_dir))
        if timed_out:
            return BoundedResult(ok=False, timed_out=True, error="timeout")
        if args[0] == "status":
            return BoundedResult(ok=ok, stdout=status, returncode=0 if ok else 1, error=None if ok else "exit 1")
        if args[0] == "worktree":
            return BoundedResult(ok=True, stdout=f"worktree {cwd}\n")
        return BoundedResult(ok=False, error="unavailable")
    return runner


class ScanTestBase(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.base = self.state.parent
        self.projects = Path(os.path.realpath(self.base / "projects"))
        self.projects.mkdir()
        self.fake_home = Path(os.path.realpath(self.base / "home"))
        self.fake_home.mkdir()
        write_roots(self.state, self.projects)

    def run_scan(self, payload=None, **dep_kwargs):
        dep_kwargs.setdefault("excludes_file", lambda: None)  # hermetic: never read the real global git config
        deps = ScanDeps(home=self.fake_home, **dep_kwargs)
        return run_dev_hq_scan(payload if payload is not None else {}, state_base=self.state, deps=deps)

    def repo_by_name(self, result, name):
        return next(r for r in result["repositories"] if r["name"] == name)


class RootApprovalTests(ScanTestBase):
    def test_valid_approved_root_scans_complete(self):  # 1
        make_repo(self.projects / "alpha")
        result = self.run_scan()
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["roots_scanned"], 1)
        self.assertEqual(result["roots"], [str(self.projects)])
        self.assertEqual(result["summary"]["repositories"], 1)
        self.assertEqual(result["scan_type"], "dev_hq_scan")
        self.assertEqual(result["schema_version"], 1)

    def test_no_approved_roots_fails_clearly(self):  # 2
        (self.state / scan.ROOTS_FILENAME).unlink()
        with self.assertRaises(ScanDenied) as cm:
            self.run_scan()
        self.assertIn("no approved development roots", cm.exception.reason)
        self.assertTrue(cm.exception.permanent)
        write_roots(self.state)  # empty list
        with self.assertRaises(ScanDenied):
            self.run_scan()

    def test_requested_roots_can_narrow_but_not_widen(self):
        make_repo(self.projects / "inside" / "alpha")
        make_repo(self.base / "elsewhere" / "beta")
        result = self.run_scan({"roots": [str(self.projects / "inside")]})
        self.assertEqual([r["name"] for r in result["repositories"]], ["alpha"])
        with self.assertRaises(ScanDenied):
            self.run_scan({"roots": [str(self.base / "elsewhere")]})
        with self.assertRaises(ScanDenied):
            self.run_scan({"roots": [str(self.projects / "..")]})

    def test_approved_root_that_was_replaced_by_a_symlink_is_not_scanned(self):  # review finding 4
        second = self.base / "projects2"
        second.mkdir()
        second = Path(os.path.realpath(second))  # approvals are stored canonical
        make_repo(second / "beta")
        make_repo(self.projects / "alpha")
        write_roots(self.state, self.projects, second)
        moved = self.base / "projects-moved"
        os.rename(self.projects, moved)
        self.projects.symlink_to(moved)  # the approved path now resolves somewhere else
        result = self.run_scan()
        self.assertEqual(result["roots"], [str(second)])
        self.assertEqual([r["name"] for r in result["repositories"]], ["beta"])
        self.assertIn("approved_root_moved", [w["code"] for w in result["warnings"]])
        write_roots(self.state, self.projects)  # only the moved root is approved: nothing left to scan
        with self.assertRaises(ScanDenied):
            self.run_scan()

    def test_no_roots_left_says_why_each_root_was_dropped(self):  # review W1
        write_roots(self.state, self.projects, "/")  # one root will now move, one is never allowed
        moved = self.base / "projects-moved"
        os.rename(self.projects, moved)
        self.projects.symlink_to(moved)
        with self.assertRaises(ScanDenied) as cm:
            self.run_scan()
        reason = cm.exception.reason
        self.assertIn("no approved development roots", reason)
        self.assertIn("now resolves to a different location", reason, "the moved root's reason must reach the owner")
        self.assertIn("filesystem root is not allowed", reason, "the refused root's reason must reach the owner")
        self.assertNotIn(str(self.base), reason, "reasons stay path-free")

    def test_no_roots_with_no_approvals_keeps_the_plain_message(self):
        write_roots(self.state)
        with self.assertRaises(ScanDenied) as cm:
            self.run_scan()
        self.assertEqual(
            cm.exception.reason,
            "no approved development roots: approve a root in Chief before scanning",
        )

    def test_requested_root_inside_an_excluded_folder_is_denied(self):
        for name in ("credentials", "team-secrets", ".ssh", "api_tokens"):
            inner = self.projects / name / "app"
            make_repo(inner)
            with self.subTest(name=name), self.assertRaises(ScanDenied) as cm:
                self.run_scan({"roots": [str(inner)]})
            self.assertIn("excluded", cm.exception.reason)
        ok = self.projects / "fine" / "app"
        make_repo(ok)
        self.assertEqual([r["name"] for r in self.run_scan({"roots": [str(ok)]})["repositories"]], ["app"])

    def test_requested_symlink_root_resolves_before_check(self):
        outside = self.base / "outside"
        outside.mkdir()
        link = self.projects / "sneaky"
        link.symlink_to(outside)
        with self.assertRaises(ScanDenied):
            self.run_scan({"roots": [str(link)]})

    def test_malformed_payloads_denied(self):  # 23 (daemon side)
        bad = [
            {"command": "rm -rf /"},
            {"roots": "not-a-list"},
            {"roots": ["relative/path"]},
            {"roots": [str(self.projects / "missing")]},
            {"roots": [123]},
            {"include_processes": "yes"},
            {"limits": {"max_depth": -1}},
            {"limits": {"max_depth": True}},
            {"limits": {"nope": 1}},
            {"limits": [1]},
        ]
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(ScanDenied):
                self.run_scan(payload)

    def test_limits_can_only_tighten(self):
        limits = scan.limits_from_payload({"max_depth": 999, "max_entries": 10**9, "max_seconds": 10**6})
        self.assertEqual(limits.max_depth, scan.HARD_CAPS.max_depth)
        self.assertEqual(limits.max_entries, scan.HARD_CAPS.max_entries)
        self.assertEqual(limits.max_seconds, scan.HARD_CAPS.max_seconds)
        self.assertEqual(scan.limits_from_payload({"max_depth": 2}).max_depth, 2)

    def test_roots_file_must_be_private_regular_file(self):
        write_roots(self.state, self.projects, mode=0o666)
        with self.assertRaises(ScanDenied):
            self.run_scan()
        (self.state / scan.ROOTS_FILENAME).unlink()
        real = self.base / "real-roots.json"
        real.write_text(json.dumps({"roots": [str(self.projects)]}))
        os.chmod(real, 0o600)
        (self.state / scan.ROOTS_FILENAME).symlink_to(real)
        with self.assertRaises(ScanDenied):
            self.run_scan()

    def test_excluded_and_dangerous_roots_are_rejected(self):
        ssh = self.projects / ".ssh"
        ssh.mkdir()
        library = self.fake_home / "Library" / "x"
        library.mkdir(parents=True)
        for bad in (ssh, self.fake_home, self.fake_home.parent, Path("/"), library, self.state, self.state.parent):
            with self.subTest(root=str(bad)), self.assertRaises(ScanDenied):
                scan.resolve_root(str(bad), home=self.fake_home, state_base=self.state)
        write_roots(self.state, ssh, self.fake_home)  # every approved entry is invalid
        with self.assertRaises(ScanDenied) as cm:
            self.run_scan()
        self.assertIn("no approved development roots", cm.exception.reason)

    def test_invalid_entry_ignored_with_warning_when_another_is_valid(self):
        write_roots(self.state, self.fake_home, self.projects)
        make_repo(self.projects / "alpha")
        result = self.run_scan()
        self.assertEqual(result["roots_scanned"], 1)
        self.assertIn("approved_root_invalid", [w["code"] for w in result["warnings"]])


class RepositoryInventoryTests(ScanTestBase):
    def test_discovery_and_clean_repo(self):  # 3, 5
        make_repo(self.projects / "alpha")
        make_repo(self.projects / "group" / "beta")
        (self.projects / "notes").mkdir()
        (self.projects / "notes" / "todo.txt").write_text("x")
        result = self.run_scan()
        self.assertEqual(sorted(r["name"] for r in result["repositories"]), ["alpha", "beta"])
        alpha = self.repo_by_name(result, "alpha")
        self.assertEqual(alpha["path"], str(self.projects / "alpha"))
        self.assertFalse(alpha["dirty"])
        self.assertEqual((alpha["modified_count"], alpha["untracked_count"]), (0, 0))
        self.assertEqual(alpha["branch"], "main")
        self.assertEqual(len(alpha["head"]), 7)
        self.assertEqual(result["summary"]["dirty_repositories"], 0)

    def test_dirty_working_tree(self):  # 4
        repo = make_repo(self.projects / "alpha")
        (repo / "a.txt").write_text("changed\n")
        (repo / "new.txt").write_text("new\n")
        result = self.run_scan()
        alpha = self.repo_by_name(result, "alpha")
        self.assertTrue(alpha["dirty"])
        self.assertEqual(alpha["modified_count"], 1)
        self.assertEqual(alpha["untracked_count"], 1)
        self.assertEqual(result["summary"]["dirty_repositories"], 1)
        self.assertIn("review_dirty_repositories", [r["code"] for r in result["recommendations"]])

    def test_missing_upstream_is_not_broken(self):  # 6
        make_repo(self.projects / "alpha")
        result = self.run_scan()
        alpha = self.repo_by_name(result, "alpha")
        self.assertFalse(alpha["has_upstream"])
        self.assertEqual(alpha["ahead_behind"], "unknown")
        self.assertIsNone(alpha["ahead"])
        self.assertNotIn("errors", alpha)
        self.assertEqual(result["status"], "complete")

    def test_upstream_ahead_behind_known_without_network(self):
        bare = self.base / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(bare)], check=True, env=GIT_ENV)
        repo = make_repo(self.projects / "alpha")
        git(repo, "remote", "add", "origin", str(bare))
        git(repo, "push", "-q", "-u", "origin", "main")
        (repo / "b.txt").write_text("two\n")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "second")
        alpha = self.repo_by_name(self.run_scan(), "alpha")
        self.assertTrue(alpha["has_upstream"])
        self.assertEqual((alpha["ahead"], alpha["behind"]), (1, 0))
        self.assertEqual(alpha["ahead_behind"], "known")

    def test_detached_head(self):  # 7
        repo = make_repo(self.projects / "alpha")
        git(repo, "checkout", "-q", "--detach")
        alpha = self.repo_by_name(self.run_scan(), "alpha")
        self.assertTrue(alpha["detached"])
        self.assertIsNone(alpha["branch"])
        self.assertEqual(len(alpha["head"]), 7)

    def test_unborn_repository(self):
        make_repo(self.projects / "fresh", commit=False)
        fresh = self.repo_by_name(self.run_scan(), "fresh")
        self.assertTrue(fresh["unborn"])
        self.assertIsNone(fresh["head"])

    def test_multiple_worktrees(self):  # 8
        repo = make_repo(self.projects / "alpha")
        git(repo, "worktree", "add", "-q", str(self.projects / "alpha-wt"), "-b", "wt")
        result = self.run_scan()
        alpha = self.repo_by_name(result, "alpha")
        wt = self.repo_by_name(result, "alpha-wt")
        self.assertEqual(alpha["worktree_count"], 2)
        self.assertEqual(wt["worktree_count"], 2)
        self.assertTrue(wt["linked_worktree_or_submodule"])
        self.assertFalse(alpha["linked_worktree_or_submodule"])
        self.assertEqual(result["summary"]["possible_duplicate_families"], 0)  # worktrees are not duplicates

    def test_possible_duplicate_family_needs_review_and_has_evidence(self):  # 9
        original = make_repo(self.projects / "grade-book")
        subprocess.run(["git", "clone", "-q", str(original), str(self.projects / "grade-book copy")], check=True, env=GIT_ENV)
        make_repo(self.projects / "Grade Book (2)", filename="other.txt")
        make_repo(self.projects / "unrelated")
        result = self.run_scan()
        self.assertEqual(result["summary"]["possible_duplicate_families"], 1)
        fam = result["duplicate_families"][0]
        self.assertEqual(fam["classification"], "possible_duplicate_family")
        self.assertTrue(fam["requires_owner_review"])
        self.assertEqual(len(fam["members"]), 3)
        self.assertIn("similar_name", fam["evidence"])
        self.assertIn("shared_root_commit", fam["evidence"])
        self.assertIn("includes_unrelated_history", fam["evidence"])

    def test_similar_names_with_unrelated_history_are_labelled_as_such(self):
        make_repo(self.projects / "quiz-tool")
        make_repo(self.projects / "quiz-tool-old", filename="different.txt")
        fam = self.run_scan()["duplicate_families"][0]
        self.assertIn("similar_name", fam["evidence"])
        self.assertIn("different_root_commits", fam["evidence"])
        self.assertNotIn("shared_root_commit", fam["evidence"])

    def test_normalize_name(self):
        self.assertEqual(scan.normalize_name("My App copy"), scan.normalize_name("my-app"))
        self.assertEqual(scan.normalize_name("My App (2)"), "my-app")
        self.assertNotEqual(scan.normalize_name("alpha"), scan.normalize_name("beta"))

    def test_repository_git_failure_is_reported_not_fatal(self):
        make_repo(self.projects / "alpha")
        result = self.run_scan(git=fake_git(ok=False))
        alpha = self.repo_by_name(result, "alpha")
        self.assertTrue(alpha["errors"])
        self.assertEqual(result["status"], "partial")
        self.assertIn("repository_metadata_incomplete", [w["code"] for w in result["warnings"]])


class GitSafetyTests(ScanTestBase):
    def test_git_invoked_read_only_with_safe_arguments(self):
        make_repo(self.projects / "alpha")
        calls: list = []
        self.run_scan(git=fake_git(calls=calls))
        self.assertTrue(calls)
        forbidden = {"fetch", "pull", "push", "prune", "gc", "clean", "reset", "stash", "checkout", "remote", "config"}
        for args, _cwd, timeout, cap in calls:
            self.assertTrue(set(args).isdisjoint(forbidden), args)
            self.assertIn(args[0], {"status", "worktree", "rev-list"})
            self.assertGreater(timeout, 0)
            self.assertLess(cap, 10_000_000)

    def test_real_runner_argv_and_environment(self):
        seen = {}

        def fake_run(argv, **kw):
            seen["argv"], seen["env"] = argv, kw["env"]
            return BoundedResult(ok=True, stdout=CLEAN_STATUS, returncode=0)

        with mock.patch.object(scan, "run_bounded", fake_run):
            scan._real_git_runner(["status", "--porcelain=v2"], str(self.projects), 5.0, 1000)
        argv = seen["argv"]
        self.assertIsInstance(argv, list)
        self.assertIn("core.fsmonitor=false", argv)
        self.assertIn("core.attributesFile=/dev/null", argv)
        self.assertIn("--no-optional-locks", argv)
        self.assertNotIn("--git-dir", argv, "no pin unless a validated git dir is supplied")
        self.assertEqual(seen["env"]["GIT_OPTIONAL_LOCKS"], "0")
        self.assertEqual(seen["env"]["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(seen["env"]["GIT_CONFIG_GLOBAL"], "/dev/null", "the user's global git config is never loaded")
        self.assertEqual(seen["env"]["GIT_CONFIG_NOSYSTEM"], "1")

    def test_git_dir_and_work_tree_are_pinned_for_ordinary_repositories(self):
        repo = make_repo(self.projects / "alpha")
        seen = {}

        def fake_run(argv, **kw):
            seen["argv"] = argv
            return BoundedResult(ok=True, stdout=CLEAN_STATUS, returncode=0)

        with mock.patch.object(scan, "run_bounded", fake_run):
            scan._real_git_runner(["status"], str(repo), 5.0, 1000, git_dir=str(repo / ".git"))
        argv = seen["argv"]
        self.assertEqual(argv[argv.index("--git-dir") + 1], str(repo / ".git"))
        self.assertEqual(argv[argv.index("--work-tree") + 1], str(repo))
        pins: list = []
        self.run_scan(git=fake_git(pins=pins))
        self.assertTrue(pins)
        self.assertTrue(all(gd == str(repo / ".git") for _a, _c, gd in pins), pins)

    def test_core_worktree_config_cannot_redirect_git_outside_the_root(self):
        repo = make_repo(self.projects / "alpha")
        outside = self.base / "outside-tree"
        outside.mkdir()
        for i in range(5):
            (outside / f"stray{i}.txt").write_text("x")
        git(repo, "config", "core.worktree", str(outside))
        alpha = self.repo_by_name(self.run_scan(), "alpha")
        self.assertEqual(alpha["untracked_count"], 0, "Git must look at the repository, not the redirected tree")
        self.assertFalse(alpha["dirty"])

    def test_repo_config_cannot_run_commands_via_fsmonitor(self):
        repo = make_repo(self.projects / "alpha")
        marker = self.base / "pwned"
        hook = self.base / "hook.sh"
        hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
        hook.chmod(0o755)
        git(repo, "config", "core.fsmonitor", str(hook))
        result = self.run_scan()
        self.assertFalse(marker.exists())
        self.assertEqual(self.repo_by_name(result, "alpha")["branch"], "main")

    def test_scan_does_not_modify_inspected_projects(self):
        repo = make_repo(self.projects / "alpha")
        (repo / "a.txt").write_text("dirty\n")
        (self.projects / "alpha" / "node_modules").mkdir()
        (self.projects / "alpha" / "node_modules" / "x.js").write_text("x")

        def snapshot():
            out = {}
            for p in sorted(self.projects.rglob("*")):
                st = os.lstat(p)
                out[str(p)] = (st.st_size, st.st_mtime_ns, st.st_mode)
            return out

        before = snapshot()
        self.run_scan()
        self.assertEqual(before, snapshot())


class FilesystemBoundaryTests(ScanTestBase):
    def test_symlink_escaping_root_not_followed(self):  # 10
        outside = self.base / "outside"
        make_repo(outside / "outside-project")
        make_repo(self.projects / "alpha")
        (self.projects / "link-out").symlink_to(outside)
        (self.projects / "link-in").symlink_to(self.projects / "alpha")
        result = self.run_scan()
        self.assertEqual([r["name"] for r in result["repositories"]], ["alpha"])
        self.assertEqual(result["coverage"]["symlinks_escaping_root"], 1)
        self.assertEqual(result["coverage"]["symlinks_skipped"], 2)

    @unittest.skipIf(os.geteuid() == 0, "permissions are not enforced for root")
    def test_inaccessible_directory(self):  # 11
        make_repo(self.projects / "alpha")
        locked = self.projects / "locked"
        make_repo(locked / "hidden")
        os.chmod(locked, 0)
        try:
            result = self.run_scan()
        finally:
            os.chmod(locked, 0o700)
        self.assertEqual([r["name"] for r in result["repositories"]], ["alpha"])
        self.assertGreaterEqual(result["coverage"]["inaccessible_directories"], 1)
        self.assertEqual(result["status"], "partial")

    def test_nested_excluded_secret_directories_never_entered(self):  # 12
        make_repo(self.projects / "alpha")
        for name in (".ssh", ".aws", "credentials", "team-secrets", "api_tokens", "Keychains", ".local", ".claude"):
            make_repo(self.projects / "alpha" / "sub" / name / "leak")
            make_repo(self.projects / name / "leak2")
        result = self.run_scan()
        self.assertEqual([r["name"] for r in result["repositories"]], ["alpha"])
        self.assertEqual(result["coverage"]["excluded_directories_skipped"], 16)
        self.assertNotIn("leak", json.dumps(result))

    def test_depth_limit_reports_partial(self):  # 13
        deep = self.projects / "a" / "b" / "c" / "d"
        make_repo(deep / "deep-repo")
        make_repo(self.projects / "shallow")
        result = self.run_scan({"limits": {"max_depth": 2}})
        self.assertEqual([r["name"] for r in result["repositories"]], ["shallow"])
        self.assertIn("depth_limit", result["limits_hit"])
        self.assertEqual(result["status"], "partial")
        full = self.run_scan()
        self.assertEqual(sorted(r["name"] for r in full["repositories"]), ["deep-repo", "shallow"])
        self.assertEqual(full["status"], "complete")

    def test_entry_limit_reports_partial(self):  # 14
        busy = self.projects / "busy"
        busy.mkdir()
        for i in range(100):
            (busy / f"f{i}.txt").write_text("x")
        result = self.run_scan({"limits": {"max_entries": 10}})
        self.assertIn("entry_limit", result["limits_hit"])
        self.assertLessEqual(result["coverage"]["entries_visited"], 10)
        self.assertEqual(result["status"], "partial")

    def test_repository_limit_reports_partial(self):
        for i in range(5):
            make_repo(self.projects / f"r{i}", commit=False)
        result = self.run_scan({"limits": {"max_repos": 2}})
        self.assertEqual(len(result["repositories"]), 2)
        self.assertIn("repo_limit", result["limits_hit"])
        self.assertEqual(result["status"], "partial")

    def test_overall_deadline_stops_scan(self):  # 16
        for i in range(20):
            make_repo(self.projects / f"r{i}", commit=False)
        result = self.run_scan({"limits": {"max_seconds": 3}}, clock=StepClock(1.0), git=fake_git())
        self.assertIn("deadline", result["limits_hit"])
        self.assertEqual(result["status"], "partial")
        self.assertLess(len(result["repositories"]), 20)


class StorageTests(ScanTestBase):
    def test_build_directories_measured_and_labelled(self):
        repo = make_repo(self.projects / "alpha")
        nm = repo / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_bytes(b"x" * 20_000)
        venv = repo / ".venv"
        venv.mkdir()
        (venv / "bin").write_bytes(b"y" * 5_000)
        make_repo(self.projects / "beta")
        (self.projects / "beta" / "dist").mkdir()
        result = self.run_scan()
        by_kind = {s["path"].split("/")[-1]: s for s in result["storage_findings"]}
        self.assertEqual(by_kind["node_modules"]["kind"], "node_modules")
        self.assertEqual(by_kind["node_modules"]["measurement"], "exact")
        self.assertGreaterEqual(by_kind["node_modules"]["bytes"], 20_000)
        self.assertEqual(by_kind[".venv"]["kind"], "python_venv")
        self.assertEqual(by_kind["dist"]["kind"], "build_output")
        sizes = [s["bytes"] for s in result["storage_findings"]]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(self.repo_by_name(result, "alpha")["git_dir_size"]["measurement"], "bounded_estimate")

    def test_measurement_cap_gives_partial_not_exact(self):
        repo = make_repo(self.projects / "alpha")
        nm = repo / "node_modules"
        nm.mkdir()
        for i in range(50):
            (nm / f"f{i}").write_text("x")
        ctx = scan._Ctx(scan.ScanLimits(measure_entries_per_dir=10), ScanDeps())
        size, how = scan.measure_dir(nm, ctx)
        self.assertEqual(how, "partial")
        self.assertGreater(size, 0)

    @unittest.skipIf(os.geteuid() == 0, "permissions are not enforced for root")
    def test_measurement_unavailable_for_unreadable_directory(self):
        locked = self.projects / "node_modules"
        locked.mkdir()
        os.chmod(locked, 0)
        try:
            ctx = scan._Ctx(scan.ScanLimits(), ScanDeps())
            outcome = scan.measure_dir(locked, ctx)
        finally:
            os.chmod(locked, 0o700)
        self.assertEqual(outcome, (None, "unavailable"))

    def test_large_directory_threshold_counts(self):
        with mock.patch.object(scan, "LARGE_DIR_BYTES", 1_000):
            repo = make_repo(self.projects / "alpha")
            (repo / "build").mkdir()
            (repo / "build" / "blob").write_bytes(b"z" * 50_000)
            result = self.run_scan()
        self.assertEqual(result["summary"]["large_build_directories"], 1)
        self.assertIn("review_large_build_directories", [r["code"] for r in result["recommendations"]])

    def test_symlinks_inside_build_dirs_not_followed(self):
        outside = self.base / "big"
        outside.mkdir()
        (outside / "huge").write_bytes(b"h" * 500_000)
        repo = make_repo(self.projects / "alpha")
        (repo / "node_modules").mkdir()
        (repo / "node_modules" / "link").symlink_to(outside)
        result = self.run_scan()
        nm = next(s for s in result["storage_findings"] if s["kind"] == "node_modules")
        self.assertLess(nm["bytes"], 100_000)


class BoundedSubprocessTests(unittest.TestCase):
    def test_subprocess_timeout_terminates_child(self):  # 15
        code = "import os,time;print(os.getpid(),flush=True);time.sleep(60)"
        start = time.monotonic()
        res = scan.run_bounded([sys.executable, "-c", code], timeout_s=0.6, max_bytes=1000)
        self.assertTrue(res.timed_out)
        self.assertFalse(res.ok)
        self.assertLess(time.monotonic() - start, 6)
        pid = int(res.stdout.split()[0])
        for _ in range(40):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail("timed-out child is still running")

    def test_output_cap_truncates_and_terminates(self):
        code = "import sys\nwhile True: sys.stdout.write('x'*70000); sys.stdout.flush()"
        res = scan.run_bounded([sys.executable, "-c", code], timeout_s=10, max_bytes=100_000)
        self.assertTrue(res.truncated)
        self.assertLessEqual(len(res.stdout), 100_000)

    def test_spawn_failure_is_a_result_not_an_exception(self):
        res = scan.run_bounded(["/definitely/not/a/binary"], timeout_s=1, max_bytes=10)
        self.assertFalse(res.ok)

    def test_scan_level_git_timeout_marks_partial(self):  # 15 (scan level)
        base = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(shutil.rmtree, base, True)
        state = base / "state"
        state.mkdir()
        projects = base / "projects"
        (projects / "alpha" / ".git").mkdir(parents=True)
        write_roots(state, projects)
        home = base / "home"
        home.mkdir()
        result = run_dev_hq_scan({}, state_base=state, deps=ScanDeps(home=home, git=fake_git(timed_out=True)))
        self.assertIn("git_timeout", result["limits_hit"])
        self.assertEqual(result["status"], "partial")
        self.assertIn("timed out", result["repositories"][0]["errors"][0])


class OutputTests(ScanTestBase):
    def test_oversized_output_is_trimmed_and_never_marked_complete(self):  # 17, 18
        for i in range(250):
            (self.projects / f"{'long-project-name-' * 5}{i:04d}" / ".git").mkdir(parents=True)
        result = self.run_scan({"limits": {"max_repos": 300}}, git=fake_git())
        encoded = json.dumps(result, separators=(",", ":"), sort_keys=True).encode()
        self.assertLessEqual(len(encoded), scan.RESULT_MAX_BYTES)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["status"], "partial")
        self.assertIn("output_truncated", result["limits_hit"])
        self.assertGreater(result["omitted"]["repositories"], 0)
        self.assertEqual(result["summary"]["repositories"], 250)  # totals stay honest
        self.assertEqual(len(result["repositories"]) + result["omitted"]["repositories"], 250)
        self.assertIn("scan_was_partial", [r["code"] for r in result["recommendations"]])

    def test_report_is_deterministic_apart_from_timestamps(self):
        make_repo(self.projects / "b")
        make_repo(self.projects / "a")
        (self.projects / "a" / "dist").mkdir()

        def normalised():
            r = self.run_scan()
            r.pop("started_at")
            r.pop("finished_at")
            return json.dumps(r, sort_keys=True)

        self.assertEqual(normalised(), normalised())

    def test_recommendations_are_text_only(self):
        repo = make_repo(self.projects / "alpha")
        (repo / "x.txt").write_text("x")
        for rec in self.run_scan()["recommendations"]:
            self.assertEqual(set(rec), {"code", "severity", "message"})
            self.assertNotRegex(rec["message"], r"(rm -|sudo|git (clean|reset)|`)")


class ProcessSnapshotTests(ScanTestBase):
    PS = "\n".join(
        [
            "  100     1  900000   2-03:04:05 /usr/local/bin/node",
            "  101   100  800000      00:10:00 /usr/local/bin/node",
            "  102     1 7000000   5-00:00:00 /Applications/Ollama.app/Contents/Resources/ollama",
            "  103     1  300000   1-00:00:00 /opt/homebrew/bin/python3.12",
            "  104     1  100000      00:05:00 /opt/homebrew/bin/python3.12",
            "  105     1  400000   2-00:00:00 /usr/bin/Safari",
            "  106     1  500000   1-00:00:00 /Applications/Xcode.app/Contents/Developer/Library/CoreSimulator/CoreSimulatorService",
            "  107    50  200000     03:00:00 /Users/x/.local/bin/claude",
            "garbage line",
        ]
    )

    def test_snapshot_categories_and_stale_rules(self):
        make_repo(self.projects / "alpha")
        result = self.run_scan({"include_processes": True}, ps=lambda _t: self.PS)
        findings = result["process_findings"]
        mem = {f["pid"]: f for f in findings if f["finding"] == "process_memory"}
        self.assertEqual(mem[102]["category"], "ollama")
        self.assertEqual(mem[100]["category"], "node_js")
        self.assertEqual(mem[103]["category"], "python")
        self.assertEqual(mem[106]["category"], "simulator")
        self.assertEqual(mem[107]["category"], "coding_agent")
        self.assertNotIn(105, mem)  # unrelated apps are not reported
        stale = {f["pid"] for f in findings if f["finding"] == "possible_stale_process"}
        self.assertEqual(stale, {100, 103})  # orphaned (ppid 1) and old; ollama/young/non-dev excluded
        for f in findings:
            self.assertEqual(
                set(f) - {"evidence", "requires_owner_review"},
                {"finding", "pid", "name", "category", "rss_bytes", "collected_at"},
            )
        self.assertIn("review_possible_stale_processes", [r["code"] for r in result["recommendations"]])
        self.assertEqual(mem[102]["rss_bytes"], 7_000_000 * 1024)

    def test_never_labels_anything_confirmed_orphan(self):
        result = self.run_scan({"include_processes": True}, ps=lambda _t: self.PS)
        self.assertNotIn("orphan", json.dumps(result).lower())

    def test_snapshot_unavailable_is_a_warning_not_a_failure(self):
        make_repo(self.projects / "alpha")
        result = self.run_scan({"include_processes": True}, ps=lambda _t: None)
        self.assertEqual(result["process_findings"], [])
        self.assertIn("process_snapshot_unavailable", [w["code"] for w in result["warnings"]])
        self.assertEqual(result["summary"]["repositories"], 1)

    def test_processes_off_by_default(self):
        called = []
        result = self.run_scan(ps=lambda _t: called.append(1) or self.PS)
        self.assertEqual(result["process_findings"], [])
        self.assertFalse(called)

    def test_real_ps_never_requests_arguments_or_environment(self):
        seen = {}

        def fake_run(argv, **kw):
            seen["argv"], seen["env"] = argv, kw.get("env")
            return BoundedResult(ok=True, stdout="")

        with mock.patch.object(scan, "run_bounded", fake_run):
            scan._real_ps(2.0)
        self.assertEqual(seen["argv"], ["/bin/ps", "-axo", "pid=,ppid=,rss=,etime=,comm="])
        self.assertEqual(set(seen["env"]), {"PATH", "LANG", "LC_ALL"})  # no inherited environment

    def test_etime_parser(self):
        self.assertEqual(scan._etime_seconds("2-03:04:05"), ((2 * 24 + 3) * 60 + 4) * 60 + 5)
        self.assertEqual(scan._etime_seconds("10:00"), 600)
        self.assertEqual(scan._etime_seconds("01:00:00"), 3600)
        self.assertIsNone(scan._etime_seconds("nonsense"))


class GitFilterAndRedirectTests(ScanTestBase):
    """Review findings 1 and 2, with real throwaway repositories. Each test first proves with stock
    Git that the fixture really is dangerous, then that the scan is not affected."""

    def _outside_tree(self, name="outside-tree") -> Path:
        tree = self.base / name
        tree.mkdir()
        for i in range(5):
            (tree / f"stray{i}.txt").write_text("x")
        return tree

    def test_globally_configured_filter_is_never_run_and_global_ignores_still_apply(self):  # finding 1
        home = self.base / "ghome"
        home.mkdir()
        (home / ".gitignore_global").write_text(".DS_Store\n")

        def write_global(marker: Path) -> None:
            (home / ".gitconfig").write_text(
                f"[core]\n\texcludesFile = {home}/.gitignore_global\n"
                f"[filter \"x\"]\n\tclean = sh -c 'touch {marker} && cat'\n"
            )

        def build(repo: Path) -> None:
            make_repo(repo)
            (repo / ".gitattributes").write_text("*.txt filter=x\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", "attrs")
            edit_same_size(repo / "a.txt", "two\n")  # Git must hash it to compare
            (repo / ".DS_Store").write_text("junk")

        canary_marker, scan_marker = self.base / "canary-ran", self.base / "scan-ran"
        canary = self.base / "canary-repo"
        build(canary)
        write_global(canary_marker)
        stock_git(canary, "status", "--porcelain", home=home)
        self.assertTrue(canary_marker.exists(), "canary: stock Git runs a globally configured clean filter here")

        build(self.projects / "alpha")
        write_global(scan_marker)
        with mock.patch.dict(os.environ, {"HOME": str(home)}):
            result = self.run_scan(excludes_file=scan.resolve_global_excludes)
        self.assertFalse(scan_marker.exists(), "the scan must not run a filter from the user's global config")
        alpha = self.repo_by_name(result, "alpha")
        self.assertEqual(alpha["modified_count"], 1)
        self.assertEqual(alpha["untracked_count"], 0, "the user's global ignore file must still apply (.DS_Store)")
        self.assertNotIn("errors", alpha)

    def test_repo_local_filter_and_include_are_refused_and_never_run(self):  # finding 1
        def build(repo: Path, marker_a: Path, marker_b: Path) -> None:
            make_repo(repo)
            (repo / ".gitattributes").write_text("*.txt filter=x\n*.md filter=y\n")
            (repo / "b.md").write_text("b\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-q", "-m", "attrs")
            extra = self.base / f"extra-{repo.name}.cfg"
            extra.write_text(f"[filter \"y\"]\n\tclean = sh -c 'touch {marker_b} && cat'\n")
            with open(repo / ".git" / "config", "a") as fh:  # written directly, as an attacker or tool would
                fh.write(f"[filter \"x\"]\n\tclean = sh -c 'touch {marker_a} && cat'\n[include]\n\tpath = {extra}\n")
            edit_same_size(repo / "a.txt", "two\n")
            edit_same_size(repo / "b.md", "c\n")

        c_a, c_b = self.base / "canary-a", self.base / "canary-b"
        s_a, s_b = self.base / "scan-a", self.base / "scan-b"
        canary = self.base / "canary-repo"
        build(canary, c_a, c_b)
        stock_git(canary, "status", "--porcelain", home=self.fake_home)
        self.assertTrue(c_a.exists(), "canary: stock Git runs the repo-local clean filter")
        self.assertTrue(c_b.exists(), "canary: stock Git runs the filter pulled in through include.path")

        build(self.projects / "alpha", s_a, s_b)
        result = self.run_scan()
        self.assertFalse(s_a.exists(), "repo-local filter.* must not run during a scan")
        self.assertFalse(s_b.exists(), "a filter reached through include.path must not run during a scan")
        alpha = self.repo_by_name(result, "alpha")
        self.assertIn("not inspected", alpha["errors"][0])
        self.assertIn("filters or includes", alpha["errors"][0])
        self.assertNotIn("branch", alpha)
        self.assertEqual(result["status"], "partial")
        self.assertNotIn(str(self.base / "extra-alpha.cfg"), json.dumps(result), "config values are never reported")

    def test_unsafe_config_sections_are_recognised_and_benign_config_is_not(self):
        git_dir = self.projects / "x" / ".git"
        git_dir.mkdir(parents=True)
        cand = scan._Candidate(self.projects / "x", "dir")
        unsafe = [
            "[include]\n\tpath = x\n",
            "[includeIf \"gitdir:/x/\"]\n\tpath = y\n",
            "[Filter \"a\"]\n\tclean = x\n",
            "[filter.b]\n\tclean = x\n",
            "[core]\n\tbare = false\n  [ filter \"c\" ]\n\tclean = x\n",
        ]
        for text in unsafe:
            (git_dir / "config").write_text(text)
            with self.subTest(config=text), self.assertRaises(scan._UnsafeRepo):
                scan._git_layout(cand, [self.projects])
        (git_dir / "config").write_text(
            "[core]\n\tbare = false\n[remote \"origin\"]\n\turl = https://u:t@example.invalid/x.git\n[branch \"main\"]\n"
        )
        self.assertEqual(scan._git_layout(cand, [self.projects]), str(git_dir))

    def test_git_file_pointing_outside_the_root_is_refused_not_followed(self):  # finding 2
        outside = self._outside_tree()
        other = make_repo(self.base / "other-repo")
        git(other, "config", "core.worktree", str(outside))
        evil = self.projects / "evil"
        evil.mkdir()
        (evil / ".git").write_text(f"gitdir: {other}/.git\n")
        canary = stock_git(evil, "status", "--porcelain=v2", home=self.fake_home)
        self.assertEqual(untracked_lines(canary.stdout), 5, "canary: stock Git follows the redirect and reads the outside tree")

        calls: list = []
        result = self.run_scan(git=fake_git(calls=calls))
        self.assertEqual(calls, [], "Git is never started for a repository whose git dir is outside the roots")
        evil_repo = self.repo_by_name(result, "evil")
        self.assertIn("outside the approved roots", evil_repo["errors"][0])
        self.assertNotIn("untracked_count", evil_repo)
        real = self.run_scan()  # and with the real Git runner
        self.assertNotIn("untracked_count", self.repo_by_name(real, "evil"))
        self.assertEqual(real["status"], "partial")

    def test_linked_worktree_config_worktree_redirect_is_pinned(self):  # finding 2
        outside = self._outside_tree()
        main = make_repo(self.projects / "main")
        git(main, "worktree", "add", "-q", str(self.projects / "wt"), "-b", "wt")
        git(main, "config", "extensions.worktreeConfig", "true")
        gitdir = Path(git(self.projects / "wt", "rev-parse", "--absolute-git-dir").strip())
        (gitdir / "config.worktree").write_text(f"[core]\n\tworktree = {outside}\n")
        canary = stock_git(self.projects / "wt", "status", "--porcelain=v2", home=self.fake_home)
        self.assertEqual(untracked_lines(canary.stdout), 5, "canary: stock Git follows config.worktree out of the root")

        pins: list = []
        self.run_scan(git=fake_git(pins=pins))
        wt_pins = [gd for _a, cwd, gd in pins if cwd == str(self.projects / "wt")]
        self.assertTrue(wt_pins and all(gd == str(gitdir) for gd in wt_pins), "the validated linked git dir is pinned")
        wt = self.repo_by_name(self.run_scan(), "wt")
        self.assertEqual(wt["untracked_count"], 0, "the redirected tree must not be read")
        self.assertEqual(wt["worktree_count"], 2)
        self.assertTrue(wt["linked_worktree_or_submodule"])
        self.assertNotIn("errors", wt)

    def test_malformed_or_dangling_git_file_is_reported_not_run(self):
        junk = self.projects / "junk"
        junk.mkdir()
        (junk / ".git").write_text("this is not a gitdir pointer\n")
        dangling = self.projects / "dangling"
        dangling.mkdir()
        (dangling / ".git").write_text(f"gitdir: {self.projects}/does-not-exist\n")
        calls: list = []
        result = self.run_scan(git=fake_git(calls=calls))
        self.assertEqual(calls, [])
        self.assertIn("not a valid gitdir pointer", self.repo_by_name(result, "junk")["errors"][0])
        self.assertIn("is missing", self.repo_by_name(result, "dangling")["errors"][0])


if __name__ == "__main__":
    unittest.main()
