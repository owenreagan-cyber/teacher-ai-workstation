"""E1 harness: runs run.py --model fake on a small subset and checks summary.json. Synthetic data only."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HARNESS = REPO_ROOT / "evals" / "harness"
sys.path.insert(0, str(HARNESS))

import checks  # noqa: E402
import run as harness_run  # noqa: E402

SUBSET = ["fp-time-001", "fp-near-001", "tc-cal-001", "cd-email-001", "inj-cal-001", "ks-session-002",
          "se-bad-001", "rb-dash-001", "ho-email-001"]
EXPECTED_SUITES = {"fast_path", "tool_choice", "cant_do_yet", "injection", "kill_switch", "sessions",
                   "robustness", "honesty"}


def harness(out_root: Path, *extra: str) -> subprocess.CompletedProcess:
    argv = [sys.executable, str(HARNESS / "run.py"), "--model", "fake", "--out-root", str(out_root),
            "--quiet", "--sample-interval", "600"]
    for case in SUBSET:
        argv += ["--case", case]
    return subprocess.run(argv + list(extra), capture_output=True, text=True, timeout=300, check=False,
                          env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(Path.home())})


class HarnessRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="cos-evals-test-")
        cls.out = Path(cls._tmp.name)
        cls.first = harness(cls.out, "--run-id", "t1-fake", "--repeat-fast-path", "1", "--long-session", "4")
        cls.second = harness(cls.out, "--run-id", "t2-fake")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def summary(self, run_id):
        return json.loads((self.out / "reports" / run_id / "summary.json").read_text())

    def test_run_succeeds_and_prints_report_path(self):
        self.assertEqual(self.first.returncode, 0, self.first.stderr[-2000:])
        self.assertIn(f"Report: {self.out / 'reports' / 't1-fake' / 'report.html'}", self.first.stdout)
        html = (self.out / "reports" / "t1-fake" / "report.html").read_text()
        self.assertIn("<svg", html)
        self.assertNotIn("http://", html.replace('xmlns="http://www.w3.org/2000/svg"', ""))
        self.assertNotIn("https://", html)

    def test_summary_shape(self):
        s = self.summary("t1-fake")
        self.assertEqual([c["id"] for c in s["certs"]], [f"CERT-00{i}" for i in range(1, 8)])
        for c in s["certs"]:
            self.assertEqual(c["status"], "PASS", c)
        self.assertEqual(set(s["suites"]), EXPECTED_SUITES)
        self.assertEqual(s["overall"]["cases"], len(SUBSET))
        self.assertEqual(s["run"]["model_mode"], "fake")
        self.assertEqual(s["run"]["model_name"], "fake-scripted")
        self.assertEqual(s["run"]["case_count"], len(SUBSET))
        self.assertTrue(s["run"]["git_sha"])
        self.assertEqual(s["run"]["real_state_dir_changes"], [])
        self.assertIsNone(s["baseline"])
        self.assertEqual(s["judge"], {"status": "not_run"})
        self.assertGreater(s["latency_ms"]["fast_path_total_ms"]["n"], 0)
        self.assertIn("p95", s["latency_ms"]["fast_path_wall_ms"])
        self.assertGreaterEqual(s["resources"]["samples"], 2)

    def test_expected_outcomes(self):
        s = self.summary("t1-fake")
        cases = s["cases"]
        for cid in SUBSET:
            self.assertIn(cid, cases)
            self.assertTrue(cases[cid]["passed"], (cid, cases[cid]["failed_checks"]))
        self.assertGreater(next(c for c in s["certs"] if c["id"] == "CERT-005")["checked"], 0)
        self.assertGreater(next(c for c in s["certs"] if c["id"] == "CERT-006")["checked"], 0)

    def test_results_records(self):
        rows = [json.loads(l) for l in (self.out / "results" / "t1-fake" / "results.jsonl").read_text().splitlines()]
        fp = next(r for r in rows if r["case_id"] == "fp-time-001")
        self.assertTrue(fp["fast_path"])
        self.assertEqual(fp["model_calls"], 0)
        self.assertEqual(fp["judge"], {"status": "not_run"})
        for key in ("case_id", "suite", "prompt", "turn", "answer", "tools_used", "fast_path", "model",
                    "notices", "exit_code", "total_ms", "model_calls", "checks", "judge"):
            self.assertIn(key, fp)
        near = next(r for r in rows if r["case_id"] == "fp-near-001")
        self.assertFalse(near["fast_path"])
        self.assertGreaterEqual(near["model_calls"], 1)
        ks = [r for r in rows if r["case_id"] == "ks-session-002"]
        self.assertEqual([r["exit_code"] for r in ks], [0, 0, 3, 0])

    def test_soak_and_long_session(self):
        s = self.summary("t1-fake")
        soak = s["soak_fast_path"]
        self.assertEqual(soak["repeat"], 1)
        self.assertEqual(soak["failing_runs"], 0)
        self.assertEqual(soak["nondeterministic_cases"], {})
        self.assertEqual(soak["audit_chain"], "ok")
        ls = s["long_session"]
        self.assertEqual((ls["turns_recorded"], ls["skipped_lines"], ls["failing_turns"]), (4, 0, 0))
        self.assertTrue(ls["samples"])

    def test_second_run_compares_with_first(self):
        self.assertEqual(self.second.returncode, 0, self.second.stderr[-2000:])
        b = self.summary("t2-fake")["baseline"]
        self.assertEqual(b["run_id"], "t1-fake")
        self.assertEqual((b["new_failures"], b["fixed"], b["cert_changes"]), ([], [], []))


class SuiteFileTests(unittest.TestCase):
    def test_suites_load_with_unique_ids(self):
        cases = harness_run.load_cases(None, None)
        by_suite = {}
        for c in cases:
            by_suite[c["suite"]] = by_suite.get(c["suite"], 0) + 1
        self.assertEqual(set(by_suite), EXPECTED_SUITES)
        self.assertGreaterEqual(len(cases), 150)
        for c in cases:
            self.assertTrue((REPO_ROOT / "evals" / "fixtures" / c.get("fixtures", "default")).is_dir(), c["id"])

    def test_fixture_titles_are_obviously_synthetic(self):
        for name in ("default", "injection"):
            base = REPO_ROOT / "evals" / "fixtures" / name
            events = json.loads((base / "calendar.json").read_text())["events"]
            rems = json.loads((base / "reminders.json").read_text())["reminders"]
            if name == "default":
                for item in events + rems:
                    self.assertTrue(item["title"].startswith("Test "), item["title"])
            for item in events + rems:
                self.assertTrue(item["calendar" if "calendar" in item else "list"].startswith("Test "))


class FakeModelSafetyTests(unittest.TestCase):
    def test_fake_cos_refuses_outside_fixture_mode(self):
        res = subprocess.run([sys.executable, "-s", "-E", "-P", str(HARNESS / "fake_cos.py"), "status"],
                             capture_output=True, text=True, timeout=60, check=False,
                             env={"PATH": "/usr/bin:/bin", "HOME": str(Path.home())})
        self.assertEqual(res.returncode, 2)
        self.assertIn("only in fixture mode", res.stderr)

    def test_fake_model_is_not_importable_from_cos(self):
        for path in (REPO_ROOT / "cos").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("fake_model", text, path)
            self.assertNotIn("evals", text.replace("evals/", "").replace("evals harness", ""), path)


class CheckTests(unittest.TestCase):
    def obs(self, **kw):
        base = {"command": "ask", "answer": "", "tools_used": [], "fast_path": False, "exit_code": 0,
                "audit": [], "stdout": "", "stderr": "", "wall_ms": 1, "total_ms": 1, "chain_status": "ok",
                "kill_switch_set": False, "session_lines_before": 0, "session_lines_after": 0}
        return {**base, **kw}

    def failed(self, results):
        return {c["name"] for c in results if not c["ok"]}

    def test_side_effect_gate_flags_allowed_write(self):
        audit = [{"kind": "decision", "subject": "tool_call", "tool": "mail_send", "allowed": True, "fixture": True}]
        res = checks.check_turn({}, self.obs(audit=audit), {"side_effects": {"time.now": "none"}})
        self.assertIn("side_effect_gate", self.failed(res))

    def test_nonlocal_model_host_and_unflagged_record(self):
        audit = [{"kind": "model_call", "host": "api.example.com:443"}]
        res = checks.check_turn({}, self.obs(audit=audit), {})
        self.assertTrue({"model_host_local", "audit_fixture_flag"} <= self.failed(res))

    def test_kill_switch_quiet(self):
        audit = [{"kind": "tool_result", "fixture": True}]
        res = checks.check_turn({}, self.obs(kill_switch_set=True, answer="x", audit=audit,
                                             session_lines_after=1), {})
        bad = next(c for c in res if c["name"] == "kill_switch_quiet")
        self.assertFalse(bad["ok"])
        self.assertEqual(bad["cert"], "CERT-005")

    def test_honesty_not_contains_feeds_cert_006(self):
        res = checks.check_turn({"answer_not_contains": ["you have 3 unread"]},
                                self.obs(answer="You have 3 unread emails."), {"suite": "honesty"})
        c = next(c for c in res if c["name"] == "answer_not_contains")
        self.assertEqual((c["ok"], c.get("cert")), (False, "CERT-006"))

    def test_answer_matching_is_case_and_quote_insensitive(self):
        res = checks.check_turn({"answer_contains": ["can't"]}, self.obs(answer="I CAN’T do that."), {})
        self.assertNotIn("answer_contains", self.failed(res))


if __name__ == "__main__":
    unittest.main()
