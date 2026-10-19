"""Request sorting (cos/intent.py), the fixed answers (cos/capabilities.py), and the paths they
pick (cos/respond.py). Synthetic data only."""
from __future__ import annotations

import contextlib
import io
import json
import os
from unittest import mock

from support import REPO_ROOT, StateDirTest

from cos import cli, intent
from cos.capabilities import NOT_BUILT, capabilities_answer
from cos.intent import LABELS, Route, classify, classify_rules
from cos.model import ModelClient

FIXTURES = REPO_ROOT / "evals" / "fixtures" / "default"

LABELED = {
    "local_files": ["find files relating to shurley on my mac", "find the file about the field trip",
                    "what's in my Documents folder", "anything in Downloads about the permission slip",
                    "look in iCloud Drive for the spelling list", "where are my files for science",
                    "find the pdf from the district"],
    "mail": ["how many emails do i have", "how many unread emails do I have", "check my email",
             "anything new in my inbox?", "what did the principal email me about this morning",
             "Send an email to the front office saying I'll be late tomorrow",
             "email the front office that I'm running late", "reply to the last email from the office"],
    "capabilities": ["what can you do?", "What else can Chief do", "what are your capabilities",
                     "where are your settings?", "how do I change your settings", "what's connected", "help"],
    "brief": ["brief", "Today's brief", "daily brief", "morning brief", "my brief", "show me my brief",
              "give me the brief"],
    "social": ["thanks!", "thank you", "ok", "got it", "cool", "hi", "good morning chief"],
    "weather": ["do the kids need jackets for recess?", "will it rain during the field trip tomorrow",
                "what's the forecast for the weekend", "make sure you tell me the city", "use my location",
                "what city is that"],
    "mac_status": ["how can I free up disk space on my mac?", "is my battery going to last the afternoon?",
                   "how much memory is free"],
    "web_lookup": ["when do the ny rangers play?", "who won the game last night", "latest news on the hurricane",
                   "what's the stock price of apple"],
    "calendar": ["what's on my calendar today?", "is there anything about email on my calendar?",
                 "when is the next field trip", "what time is my meeting", "am I busy at 3"],
    "reminders": ["anything due on my reminders?", "what's overdue"],
    "time": ["what time is it in tokyo", "how many days until thanksgiving"],
    "general": ["empty the trash on my mac", "what should I work on next", "draft a note to parents about picture day",
                "explain photosynthesis for 4th graders"],
}


class RuleTests(StateDirTest):
    def test_labels(self):
        for label, messages in LABELED.items():
            for m in messages:
                with self.subTest(m=m):
                    hit = classify_rules(m)
                    self.assertIsNotNone(hit, m)
                    self.assertEqual(hit.label, label, (m, hit))

    def test_every_label_is_known(self):
        self.assertEqual(set(LABELED), set(LABELS))
        self.assertEqual([r[1] for r in intent.RULES if r[1] not in LABELS], [])

    def test_personal_questions_are_never_web_lookups(self):
        for m in ("what did I eat for lunch today", "when did I play the video for class",
                  "who won the game I had on tv"):
            with self.subTest(m=m):
                route = classify(m, model_label=lambda *_: "web_lookup")  # even if the model says so
                self.assertEqual(route.label, "general", route)


class ModelFallbackTests(StateDirTest):
    def test_model_only_when_no_pattern(self):
        calls = []

        def model(message, previous):
            calls.append((message, previous))
            return "web_lookup"
        self.assertEqual(classify("what's on my calendar today?", model_label=model).source, "pattern")
        self.assertEqual(calls, [])
        route = classify("how tall is mount mitchell", {"question": "hi", "intent": "social"}, model_label=model)
        self.assertEqual((route.label, route.source), ("web_lookup", "model"))
        self.assertEqual(calls, [("how tall is mount mitchell", "hi")])

    def test_invalid_model_label_is_general(self):
        for bad in (None, "delete_files", "", "WEB_LOOKUP"):
            with self.subTest(bad=bad):
                self.assertEqual(classify("tell me a story", model_label=lambda *_: bad), Route("general", "default"))

    def test_parse_label(self):
        self.assertEqual(intent.parse_label('{"label": "mail"}'), "mail")
        for bad in ("mail", '{"label": "send"}', "[]", "", None, '{"label": 3}'):
            self.assertIsNone(intent.parse_label(bad), bad)

    def test_classifier_sees_only_owens_words(self):
        msgs = intent.model_messages("and the islanders?", "when do the ny rangers play?")
        self.assertEqual(msgs[0]["content"], intent.CLASSIFY_PROMPT)
        self.assertEqual(msgs[1], {"role": "user", "content": "Previous message from Owen: when do the ny rangers play?\n"
                                                               "Message to sort: and the islanders?"})
        self.assertEqual(intent.CLASSIFY_SCHEMA["properties"]["label"]["enum"], list(LABELS))


class FollowUpTests(StateDirTest):
    def test_follow_ups_continue_the_previous_label(self):
        for prev, msg in (("weather", "and tomorrow?"), ("weather", "do that for me"), ("web_lookup", "and the Islanders?"),
                          ("calendar", "what about friday?"), ("weather", "same for work")):
            with self.subTest(msg=msg):
                route = classify(msg, {"question": "x", "intent": prev})
                self.assertEqual((route.label, route.source), (prev, "follow_up"))

    def test_not_follow_ups(self):
        self.assertEqual(classify("and what can you do?", {"question": "x", "intent": "capabilities"}).label,
                         "capabilities")  # fixed answers are not continued
        self.assertEqual(classify("and check my email please, then tell me about the weather on friday",
                                  {"question": "x", "intent": "weather"}).source, "pattern")  # too long
        self.assertEqual(classify("do that for me", None, model_label=lambda *_: None).label, "general")


class CapabilityAnswerTests(StateDirTest):
    def test_not_built_answers_are_fixed(self):
        self.assertEqual(NOT_BUILT["local_files"], "I can't search files on your Mac yet. That's coming in a later build.")
        self.assertEqual(NOT_BUILT["mail"], "Mail isn't connected yet, so I can't see your inbox.")

    def test_capabilities_from_registry_and_config(self):
        from cos import fixture
        cfg = self.config(fixture_dir=FIXTURES)
        reg = fixture.build_fixture_registry(fixture.fixture_context(cfg))
        text = capabilities_answer(reg, cfg)
        for want in ("tell the time", "read today's calendar", "search the web", "Connected:", "qwen3.6:35b",
                     "Not built yet: searching files on your Mac, and mail.", "can't send",
                     "there's no settings screen yet", "config.json in the Chief state folder"):
            self.assertIn(want, text)
        self.assertNotRegex(text.lower(), r"settings (?:>|→)|preferences (?:>|→)|menu bar → settings|click settings")

    def test_only_registered_tools_are_claimed(self):
        from cos.registry import Registry
        text = capabilities_answer(Registry(), self.config())
        self.assertNotIn("calendar", text.split("Connected:")[0])
        self.assertNotIn("search the web", text)


class ResponderPathTests(StateDirTest):
    """cos ask in fixture mode (synthetic data): fixed answers make no model call and no web search."""

    def ask(self, question, model_calls_allowed=False):
        os.environ["COS_FIXTURE_DIR"] = str(FIXTURES)
        self.addCleanup(os.environ.pop, "COS_FIXTURE_DIR", None)
        out, err = io.StringIO(), io.StringIO()
        boom = mock.patch.object(ModelClient, "chat", side_effect=AssertionError("no model call"))
        with boom, contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(["ask", "--json", "--", question])
        self.assertEqual(code, 0, err.getvalue())
        audit = [json.loads(l) for l in (self.state / "audit.jsonl").read_text().splitlines()]
        return json.loads(out.getvalue()), audit

    def test_fixed_paths(self):
        for q, label, text in (("find files relating to shurley on my mac", "local_files", NOT_BUILT["local_files"]),
                               ("how many emails do i have", "mail", NOT_BUILT["mail"]),
                               ("email the front office that I'm running late", "mail", NOT_BUILT["mail_send"])):
            with self.subTest(q=q):
                res, audit = self.ask(q)
                self.assertEqual((res["answer"], res["intent"], res["tools_used"], res["fast_path"]),
                                 (text, label, [], True))
                kinds = [r["kind"] for r in audit]
                self.assertNotIn("model_call", kinds)
                self.assertFalse([r for r in audit if str(r["kind"]).startswith("egress")])
                (self.state / "audit.jsonl").unlink()
                (self.state / "audit.jsonl.head").unlink(missing_ok=True)

    def test_capabilities_and_brief(self):
        res, _ = self.ask("what can you do?")
        self.assertEqual(res["intent"], "capabilities")
        self.assertIn("no settings screen", res["answer"])
        for q in ("brief", "today's brief"):
            with self.subTest(q=q):
                res, _ = self.ask(q)
                self.assertEqual(res["intent"], "brief")
                self.assertTrue(res["answer"].startswith("Daily Brief — Thursday, October 1, 2026"))
                self.assertIn("Calendar (", res["answer"])
                self.assertIn("calendar.today", res["tools_used"])

    def test_typed_search_about_local_things_is_not_a_web_search(self):
        for q, label in (("search my calendar", "calendar"), ("search my files for the field trip form", "local_files"),
                         ("look up my inbox", "mail")):
            with self.subTest(q=q):
                if label == "calendar":
                    continue  # the calendar path needs the model; covered by ws-cal-001 in the harness
                res, audit = self.ask(q)
                self.assertEqual(res["intent"], label)
                self.assertNotIn("web.search", res["tools_used"])
                self.assertFalse([r for r in audit if str(r["kind"]).startswith("egress")])


class SectionFourRoutingTests(StateDirTest):
    def test_questions_about_an_earlier_answer_are_not_web_lookups(self):
        for m in ("what did that search say?", "what do those results mean", "summarize your last answer"):
            with self.subTest(m=m):
                self.assertEqual(classify(m, model_label=lambda *_: "web_lookup").label, "general")

    def test_a_follow_up_naming_another_topic_takes_that_topic(self):
        self.assertEqual(classify("and my reminders?", {"question": "x", "intent": "weather"}).label, "reminders")
        self.assertEqual(classify("and tomorrow?", {"question": "x", "intent": "weather"}).label, "weather")

    def test_reminder_lists_are_written_by_code(self):
        from cos.intent import REMINDER_LIST
        from cos.respond import reminders_text
        for m in ("what reminders are due", "any reminders due?", "how many reminders do I have due", "and my reminders?"):
            self.assertIsNotNone(REMINDER_LIST.fullmatch(intent.normalize(m)), m)
        for m in ("which reminder is due latest today?", "remind me to grade at 3", "delete my reminder"):
            self.assertIsNone(REMINDER_LIST.fullmatch(intent.normalize(m)), m)
        self.assertEqual(reminders_text({"reminders": [{"title": "Test Reminder A", "overdue": True, "due": "Tue Sep 29"},
                                                       {"title": "Test Reminder B", "due": "4:00 PM"}]}),
                         "2 reminders due:\n- “Test Reminder A” (overdue since Tue Sep 29)\n"
                         "- “Test Reminder B” (due 4:00 PM)")
        self.assertEqual(reminders_text({"reminders": []}), "No reminders are due.")
        self.assertEqual(reminders_text({"error": "EventKit access denied"}), "Reminders are unavailable: EventKit access denied.")


class SchoolDataTests(StateDirTest):
    def test_owens_school_data_is_never_searched(self):
        for m in ("what's my Canvas assignment completion rate this week", "how many students are absent today",
                  "what are my class grades", "show my roster"):
            with self.subTest(m=m):
                self.assertNotEqual(classify(m, model_label=lambda *_: "web_lookup").label, "web_lookup")
