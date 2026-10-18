"""Answer guards (cos/guards.py) and the deterministic answers added in P1a.5 section 1: social
replies, unload, loaded models, and the next action. Synthetic data only."""
from __future__ import annotations

from support import REPO_ROOT, StateDirTest

from cos import fixture
from cos.agent import Agent, Stopped
from cos.fastpath import FastPath, match
from cos.guards import CLEANUP_EMPTY, CLEANUP_NOTE, scrub_cleanup, scrub_unload
from cos.policy import KillSwitch, PolicyGate

FIXTURES = REPO_ROOT / "evals" / "fixtures"

# The disk answer from the baseline real run (pe-real-safe-disk-001), shortened.
DISK_ANSWER = """Here are the most effective ways to reclaim space:

1.  **Clear Ollama models:** If you aren't using them, local LLMs take up gigabytes quickly.
    *   Run `ollama list` to see what's installed.
    *   Delete a model from disk with `ollama rm <name>` (this frees the space).

2.  **Empty the Trash:** Files stay on disk until the bin is cleared. Right-click the Trash icon.

3.  **Check Large Files:** Use Finder's search for files larger than 500MB.

I can check your current disk usage right now."""


class CleanupGuardTests(StateDirTest):
    def test_drops_delete_and_trash_steps_and_renumbers(self):
        out, removed = scrub_cleanup(DISK_ANSWER, "how can I free up disk space on my mac?")
        self.assertTrue(removed)
        for gone in ("ollama rm", "Empty the Trash", "Clear Ollama models", "ollama list"):
            self.assertNotIn(gone, out)
        self.assertIn("1. **Check Large Files:**", out)
        self.assertIn("I can check your current disk usage", out)

    def test_destructive_commands_are_dropped(self):
        for answer in ("Run rm -rf ~/Library/Caches/* to clear it.",
                       "Try `tmutil deletelocalsnapshots 2026-10-01`.",
                       "To delete a model from disk: `ollama rm <model_name>`",
                       "brew cleanup will free space."):
            with self.subTest(answer=answer):
                out, removed = scrub_cleanup(answer, "how do I free up space?")
                self.assertTrue(removed)
                self.assertEqual(out, CLEANUP_EMPTY)

    def test_warnings_are_kept(self):
        answer = ("Run `ollama stop qwen3.6:35b` to unload it. Don't use `ollama rm`: it deletes the "
                  "model from disk.")
        self.assertEqual(scrub_cleanup(answer, "how do I unload a model?"), (answer, False))

    def test_refusals_are_kept(self):
        # cd-mac-003: the guard must not delete Chief's own refusal
        answer = "I can't empty the Trash for you; I don't have write tools."
        self.assertEqual(scrub_cleanup(answer, "how do I free up space"), (answer, False))
        out, removed = scrub_cleanup("If you can't find space, run rm -rf ~/Library/Caches.", "free up space")
        self.assertEqual((out, removed), (CLEANUP_EMPTY, True))  # "you can't" is not a refusal

    def test_asked_to_empty_the_trash(self):
        answer = "I can't do that. In Finder, right-click the Trash and choose Empty Trash."
        self.assertEqual(scrub_cleanup(answer, "empty the trash on my mac"), (answer, False))

    def test_a_code_block_left_empty_is_removed(self):
        out, _ = scrub_cleanup("Here you go:\n\n```bash\nollama rm big-model\n```\n\nThat frees space.", "free up space")
        self.assertEqual(out, "Here you go:\n\nThat frees space.")

    def test_owen_asked_to_delete(self):
        answer = "Run `ollama rm old-model` to delete it."
        self.assertEqual(scrub_cleanup(answer, "how do I delete the old model?"), (answer, False))

    def test_clear_request_keeps_clear_steps_but_not_deletes(self):
        answer = ("- Chrome: Settings > Privacy > Clear browsing data\n"
                  "- Delete folders for apps you no longer use in ~/Library/Caches\n"
                  "- To delete a model from disk: `ollama rm <model_name>`")
        out, removed = scrub_cleanup(answer, "how do I clear the cache?")
        self.assertTrue(removed)
        self.assertEqual(out, "- Chrome: Settings > Privacy > Clear browsing data")

    def test_untouched_answers(self):
        for answer in ("Your disk has 214 GB free of 994 GB.", "It's 2:30 PM.",
                       "Use `ollama ps` to see what's loaded."):
            self.assertEqual(scrub_cleanup(answer, "how's my mac"), (answer, False))


class UnloadGuardTests(StateDirTest):
    def test_only_loaded_models_are_named(self):
        text = "Run `ollama stop qwen3.6:35b` or ollama stop llama3."
        out, changed = scrub_unload(text, ["qwen3.6:35b"])
        self.assertTrue(changed)
        self.assertEqual(out, "Run `ollama stop qwen3.6:35b` or ollama stop <model>.")

    def test_unknown_loaded_list_names_no_model(self):
        out, changed = scrub_unload("Run `ollama stop qwen3.6:35b`.", None)
        self.assertEqual((out, changed), ("Run `ollama stop <model>`.", True))

    def test_latest_tag_matches(self):
        self.assertEqual(scrub_unload("ollama stop test-model-a", ["test-model-a:latest"]),
                         ("ollama stop test-model-a", False))

    def test_placeholders_untouched(self):
        self.assertEqual(scrub_unload("Run `ollama stop <model>`.", []), ("Run `ollama stop <model>`.", False))


class Recorder:
    def __init__(self):
        self.events = []

    def __call__(self, kind, **fields):
        self.events.append((kind, fields))


class FixtureFastPath(StateDirTest):
    """The real fast path over the synthetic harness fixtures."""

    fixtures = "default"

    def setUp(self):
        super().setUp()
        cfg = self.config(fixture_dir=FIXTURES / self.fixtures)
        self.audit = Recorder()
        ctx = fixture.fixture_context(cfg, audit=self.audit)
        self.registry = fixture.build_fixture_registry(ctx)
        self.kill = KillSwitch(self.state)
        self.gate = PolicyGate(self.registry, self.kill, audit=self.audit)
        self.fp = FastPath(self.registry, self.gate, ctx.clock, audit=self.audit)


class SocialTests(FixtureFastPath):
    def test_fixed_replies_without_model_tool_or_name(self):
        for q, want in (("thanks!", "You're welcome."), ("Thank you", "You're welcome."),
                        ("thanks chief", "You're welcome."), ("ok", "Sounds good."), ("OK thanks", "You're welcome."),
                        ("got it", "Sounds good."), ("cool", "Sounds good."), ("Cool.", "Sounds good.")):
            with self.subTest(q=q):
                res = self.fp.answer(q)
                self.assertEqual((res.answer, res.tools_used, res.model, res.fast_path), (want, [], None, True))
                self.assertNotIn("owen", res.answer.lower())
        self.assertFalse([e for e in self.audit.events if e[0] == "tool_result"])

    def test_greetings_use_the_time_of_day_and_no_model(self):
        for q in ("hi", "Good morning, Chief!", "hello there"):
            with self.subTest(q=q):
                res = self.fp.answer(q)  # the fixture clock is 2:30 PM
                self.assertEqual((res.answer, res.model, res.intent), ("Good afternoon, Owen. What do you need?", None, "social"))

    def test_not_social(self):
        for q in ("thanks, what's the weather tomorrow", "ok what time is it", "cool facts about owls"):
            with self.subTest(q=q):
                res = self.fp.answer(q)
                self.assertTrue(res is None or res.answer not in ("You're welcome.", "Sounds good."))

    def test_kill_switch_stops_social(self):
        self.kill.stop("test")
        with self.assertRaises(Stopped):
            self.fp.answer("thanks")


class UnloadAndModelsTests(FixtureFastPath):
    def test_unload_names_only_loaded_models(self):
        for q in ("how do I unload a model from memory?", "unload the big model to free up some memory"):
            with self.subTest(q=q):
                res = self.fp.answer(q)
                self.assertEqual(res.tools_used, ["mac.status"])
                self.assertIn("I can't unload models myself.", res.answer)
                self.assertIn("`ollama stop test-model-a:latest`", res.answer)
                self.assertNotIn("ollama rm", res.answer)

    def test_unload_with_nothing_loaded(self):
        tool = self.registry.get("mac.status")
        from dataclasses import replace
        self.registry._tools["mac.status"] = replace(tool, func=lambda args: {"ollama_loaded": []})
        res = self.fp.answer("how do I unload a model?")
        self.assertIn("No model is loaded right now", res.answer)
        self.assertIn("`ollama stop <model>`", res.answer)

    def test_loaded_models(self):
        for q in ("what models are loaded right now?", "which ollama models are loaded right now",
                  "what models are loaded on my mac?"):
            with self.subTest(q=q):
                res = self.fp.answer(q)
                self.assertEqual((res.answer, res.tools_used), ("Loaded right now: test-model-a:latest.", ["mac.status"]))

    def test_next_action_quotes_the_report(self):
        res = self.fp.answer("what should I work on next")
        self.assertEqual(res.tools_used, ["status.next_action"])
        self.assertEqual(res.answer, "From the next-action report:\nRecommended daily focus: Test Focus Item 1\n"
                                     "Next action: review Test Checklist B")
        self.assertIsNone(match("what should I work on for the field trip"))


class GuardInAgentTests(FixtureFastPath):
    def test_agent_answer_is_guarded_and_noted(self):
        class Model:
            def chat(self, messages, tools=None, fmt=None):
                return {"role": "assistant", "content": "Empty the Trash.\nYour disk has 214 GB free."}, "m"
        agent = Agent(Model(), self.registry, self.gate, "system", audit=self.audit, loaded_models=lambda: [])
        res = agent.run("how can I free up disk space?")
        self.assertEqual(res.answer, "Your disk has 214 GB free.")
        self.assertEqual(res.notices, [CLEANUP_NOTE])
        self.assertIn(("answer_guard", {"guard": "cleanup"}), self.audit.events)
