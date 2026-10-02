"""Unit tests for the D1 developer safety guard, installer, and probe logic.

Run: python3 -m unittest discover -s tests -p 'test_dev_guard*.py' -v
Uses a fake HOME in a temp dir; never touches the real denied roots.
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(os.path.dirname(HERE), "tools", "dev_safety")
sys.path.insert(0, PKG)

import dev_guard  # noqa: E402
import dev_safety_probe as probe  # noqa: E402
import install_dev_guard  # noqa: E402
import render_settings  # noqa: E402

SOURCE = os.path.join(PKG, "dev_guard.py")


class FakeHome(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="dev-guard-test-")
        base = os.path.realpath(self._tmp.name)
        self.home = os.path.join(base, "home")
        self.cwd = os.path.join(base, "project")
        for rel in probe.ROOT_RELS:
            os.makedirs(os.path.join(self.home, rel))
        os.makedirs(os.path.join(self.cwd, ".claude"))
        self.links = os.path.join(base, "links")
        os.makedirs(self.links)
        os.symlink(os.path.join(self.home, ".ssh"), os.path.join(self.links, "link-to-ssh"))
        env = {k: v for k, v in os.environ.items() if k != "COS_FEATURE_WORKTREE"}
        env["CLAUDE_PROJECT_DIR"] = self.cwd
        self._env = mock.patch.dict(os.environ, env, clear=True)
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmp.cleanup()

    def decide(self, payload):
        # The fake home and project live in system temp; treat temp as unsafe so the
        # destructive-command checks see the sibling paths as outside the project.
        return dev_guard.evaluate(payload, home=self.home, temp_roots=[])

    def bash(self, cmd):
        return self.decide({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": self.cwd})


class TestSyntheticCases(FakeHome):
    """Every shared probe case, evaluated against the versioned source."""

    def test_all_cases(self):
        cases = probe.synthetic_cases(self.home, self.cwd, self.links)
        self.assertGreater(len(cases), 300)
        for c in cases:
            with self.subTest(c["id"]):
                reason = self.decide(c["payload"])
                got = "allow" if reason is None else "deny"
                self.assertEqual(got, c["expect"], reason)

    def test_required_process_forms_present(self):
        ids = {c["id"] for c in probe.synthetic_cases(self.home, self.cwd)}
        for need in ("ps:aux", "ps:-f", "ps:-F", "ps:-l", "ps:-o-args", "ps:-o-command", "ps:-ww",
                     "pgrep:-fl", "pgrep:-lf", "pgrep:-f-l", "pgrep:-fa", "pgrep:-af", "pgrep:-f-a",
                     "allow:ps-safe", "allow:pgrep", "allow:pgrep-f"):
            self.assertIn(need, ids)


class TestGitPolicy(FakeHome):
    def test_feature_worktree_allowed_only_for_exact_path(self):
        feat = os.path.join(os.path.dirname(self.cwd), "feature-wt")
        with mock.patch.dict(os.environ, {"COS_FEATURE_WORKTREE": feat}):
            self.assertIsNone(self.bash(f"git worktree add {feat}"))
            self.assertIsNone(self.bash(f"git worktree add -b feat/x {feat} HEAD"))
            self.assertIsNone(self.bash(f"git worktree remove {feat}"))
            self.assertIsNone(self.bash("git worktree add ../feature-wt"))
            self.assertIsNotNone(self.bash("git worktree add ../other-wt"))
            self.assertIsNotNone(self.bash(f"git worktree remove --force {feat}"))
            self.assertIsNotNone(self.bash("git worktree prune"))
            self.assertIsNotNone(self.bash(f"git worktree move {feat} /tmp/x"))

    def test_worktree_denied_without_feature_env(self):
        self.assertIn("COS_FEATURE_WORKTREE", self.bash("git worktree add ../x"))

    def test_reset_without_hard_allowed(self):
        self.assertIsNone(self.bash("git reset HEAD -- file.txt"))
        self.assertIsNotNone(self.bash("git reset --hard"))

    def test_commit_message_not_mistaken_for_flags(self):
        self.assertIsNone(self.bash("git commit -m 'git push --force'"))
        self.assertIsNone(self.bash("git commit -mfix"))

    def test_deny_reason_names_subcommand(self):
        self.assertEqual(self.bash("git -C /tmp -c a=b push"), "git push is denied")


class TestFilePolicy(FakeHome):
    def test_symlink_resolution(self):
        p = os.path.join(self.links, "link-to-ssh", "id_ed25519")
        self.assertIn("denied root", self.decide({"tool_name": "Read", "tool_input": {"file_path": p},
                                                  "cwd": self.cwd}))

    def test_memory_any_project(self):
        p = os.path.join(self.home, ".claude", "projects", "-Users-someone-else", "memory", "MEMORY.md")
        self.assertIsNotNone(self.decide({"tool_name": "Read", "tool_input": {"file_path": p}, "cwd": self.cwd}))
        # D1-003: every transcript under ~/.claude/projects is denied, not only memory.
        other = os.path.join(self.home, ".claude", "projects", "-x", "session.jsonl")
        self.assertIsNotNone(self.decide({"tool_name": "Read", "tool_input": {"file_path": other}, "cwd": self.cwd}))

    def test_project_claude_is_read_only(self):
        p = os.path.join(self.cwd, ".claude", "settings.json")
        self.assertIsNone(self.decide({"tool_name": "Read", "tool_input": {"file_path": p}, "cwd": self.cwd}))
        self.assertIsNotNone(self.decide({"tool_name": "Write", "tool_input": {"file_path": p, "content": ""},
                                          "cwd": self.cwd}))

    def test_unknown_tool_allowed(self):
        self.assertIsNone(self.decide({"tool_name": "WebSearch", "tool_input": {"query": "x"}, "cwd": self.cwd}))


class TestHookProcess(unittest.TestCase):
    """The hook as Claude Code runs it: JSON on stdin, decision on stdout."""

    def run_hook(self, raw):
        p = subprocess.run([sys.executable, SOURCE], input=raw.encode(), capture_output=True, timeout=30)
        return p.returncode, p.stdout.decode()

    def test_deny_output_shape(self):
        code, out = self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push"},
                                              "cwd": "/tmp"}))
        self.assertEqual(code, 0)
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertEqual(hso["permissionDecision"], "deny")
        self.assertTrue(hso["permissionDecisionReason"].startswith("[dev_guard] "))

    def test_allow_is_silent(self):
        code, out = self.run_hook(json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"},
                                              "cwd": "/tmp"}))
        self.assertEqual((code, out), (0, ""))

    def test_malformed_denied(self):
        for raw in ("", "not json", "[]", '{"tool_name": "Bash"}'):
            with self.subTest(raw=raw):
                _, out = self.run_hook(raw)
                self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")


class TestInstaller(unittest.TestCase):
    def test_install_read_only_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            dest = os.path.join(d, "cos")
            r1 = install_dev_guard.install(dest_dir=dest)
            installed = os.path.join(dest, "dev_guard.py")
            self.assertEqual(stat.S_IMODE(os.stat(installed).st_mode), 0o444)
            self.assertEqual(r1["installed_sha256"], r1["source_sha256"])
            with open(os.path.join(dest, "dev_guard.sha256")) as f:
                self.assertEqual(f.read().split()[0], r1["installed_sha256"])
            r2 = install_dev_guard.install(dest_dir=dest)  # reinstall over the read-only copy
            self.assertEqual(r1["installed_sha256"], r2["installed_sha256"])
            self.assertEqual([n for n in os.listdir(dest) if n.endswith(".tmp")], [])


class TestRenderedSettings(unittest.TestCase):
    """The committed settings files match render_settings.py and carry the sandbox rules."""

    def test_committed_files_are_current(self):
        for path, text in render_settings.render().items():
            with self.subTest(path=os.path.basename(path)):
                with open(path) as f:
                    self.assertEqual(f.read(), text, "run tools/dev_safety/render_settings.py")

    def test_sandbox_rules(self):
        for doc in (render_settings.proposed(), render_settings.lock()):
            sb = doc["sandbox"]
            self.assertTrue(sb["enabled"])
            self.assertTrue(sb["failIfUnavailable"])
            self.assertFalse(sb["allowUnsandboxedCommands"])
            self.assertNotIn("excludedCommands", sb)
            for need in ("~/.ssh", "~/.claude.json", "~/.claude/projects", "~/Downloads",
                         "~/.teacher-ai-workstation", "~/Library/Application Support/ChiefOfStaff"):
                self.assertIn(need, sb["filesystem"]["denyRead"])
            self.assertEqual(sb["filesystem"]["allowWrite"], ["/tmp", "/private/tmp"])
            for host in sb["network"]["allowedDomains"]:
                self.assertNotIn(host.split(":")[0], ("github.com", "api.github.com"))
        self.assertTrue(render_settings.lock()["sandbox"]["network"]["strictAllowlist"])

    def test_permission_rules_cover_claude_state(self):
        deny = render_settings.proposed()["permissions"]["deny"]
        for rule in ("Read(~/.claude.json)", "Edit(~/.claude/settings.json)",
                     "Read(~/.claude/settings.local.json)", "Read(~/.claude/projects/**)",
                     "Edit(~/.claude/projects/**)", "Edit(.claude/**)"):
            self.assertIn(rule, deny)

    def test_installer_installs_lock(self):
        with tempfile.TemporaryDirectory() as d:
            r = install_dev_guard.install(dest_dir=d)
            self.assertEqual(set(r["files"]), set(install_dev_guard.FILES))
            with open(os.path.join(d, "dev_guard.sha256")) as f:
                names = [line.split()[1] for line in f]
            self.assertEqual(names, list(install_dev_guard.FILES))


class TestBoundaryClassification(unittest.TestCase):
    CASE = {"id": "x", "expect": "deny", "tool": "Bash", "match": "git push r HEAD"}

    def stream(self, *events):
        return "\n".join(json.dumps(e) for e in events)

    def use(self, uid="t1", cmd="git push r HEAD"):
        return {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": uid, "name": "Bash", "input": {"command": cmd}}]}}

    def result(self, text, uid="t1", err=True):
        return {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": uid, "is_error": err, "content": text}]}}

    def test_no_attempt_is_inconclusive(self):
        parsed = probe.parse_stream(self.stream({"type": "result", "result": "I won't do that"}))
        self.assertEqual(probe.classify(self.CASE, parsed)["verdict"], "INCONCLUSIVE")

    def test_different_command_is_inconclusive(self):
        parsed = probe.parse_stream(self.stream(self.use(cmd="git status")))
        self.assertEqual(probe.classify(self.CASE, parsed)["verdict"], "INCONCLUSIVE")

    def test_hook_denial_passes(self):
        parsed = probe.parse_stream(self.stream(self.use(), self.result("[dev_guard] git push is denied")))
        r = probe.classify(self.CASE, parsed)
        self.assertEqual((r["verdict"], r["mechanism"]), ("PASS", "hook"))

    def test_rule_denial_passes(self):
        parsed = probe.parse_stream(self.stream(
            self.use(), self.result("Permission to use Bash with command git push r HEAD has been denied."),
            {"type": "result", "permission_denials": [{"tool_use_id": "t1"}]}))
        self.assertEqual(probe.classify(self.CASE, parsed)["mechanism"], "deny-rule")

    def test_not_granted_is_not_a_pass(self):
        parsed = probe.parse_stream(self.stream(
            self.use(), self.result("Claude requested permissions to use Bash, but you haven't granted it yet."),
            {"type": "result", "permission_denials": [{"tool_use_id": "t1"}]}))
        r = probe.classify(self.CASE, parsed)
        self.assertEqual((r["verdict"], r["mechanism"]), ("FAIL", "not-granted"))

    def test_executed_fails(self):
        parsed = probe.parse_stream(self.stream(self.use(), self.result("fatal: 'r' does not appear", err=True)))
        self.assertEqual(probe.classify(self.CASE, parsed)["verdict"], "FAIL")

    def test_validation_rejection_is_inconclusive(self):
        parsed = probe.parse_stream(self.stream(self.use(), self.result(
            "<tool_use_error>Claude Code settings.json validation failed after edit</tool_use_error>")))
        r = probe.classify(self.CASE, parsed)
        self.assertEqual((r["verdict"], r["mechanism"]), ("INCONCLUSIVE", "tool-error"))

    def test_redaction(self):
        self.assertEqual(probe.redact("--api-key crsr_abc123 x"), "--api-key <redacted> x")


if __name__ == "__main__":
    unittest.main()
