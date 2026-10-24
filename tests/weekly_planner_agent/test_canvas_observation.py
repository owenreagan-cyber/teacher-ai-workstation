"""Canvas read-only observation adapter tests (fake DeployClient only)."""
from __future__ import annotations

import unittest

from scripts.canvas_llm_deploy.client import FakeDeployClient
from scripts.weekly_planner_agent import canvas_observation as co
from scripts.weekly_planner_agent import snapshot as snap


class CanvasObservationTest(unittest.TestCase):
    def _client(self):
        fake = FakeDeployClient(courses={26404: {"id": 26404, "name": "Math"}})
        fake.assignment_groups[26404] = [
            {"id": "g1", "name": "Homework/Class Work"},
            {"id": "g2", "name": "Assessments"},
        ]
        fake.seed_page(26404, "q2w3", title="Q2W3 Math", body="<div>agenda</div>", front_page=True)
        fake.seed_assignment(26404, "SM5: Lesson 39 Homework", assignment_group="Homework/Class Work")
        return fake

    def test_assignments_and_groups_normalized(self) -> None:
        fake = self._client()
        obs = co.observe_canvas(fake, {"math": 26404})
        course = obs["courses"]["math"]
        self.assertEqual(len(course["assignments"]), 1)
        self.assertEqual(course["assignments"][0]["name"], "SM5: Lesson 39 Homework")
        self.assertEqual({g["name"] for g in course["assignment_groups"]},
                         {"Homework/Class Work", "Assessments"})

    def test_front_page_resolved(self) -> None:
        fake = self._client()
        obs = co.observe_canvas(fake, {"math": 26404})
        self.assertTrue(obs["courses"]["math"]["front_page"]["front_page"])

    def test_posted_vs_scheduled_vs_unknown(self) -> None:
        fake = self._client()
        fake.create_announcement(26404, title="Posted now", message="hi")
        fake.create_announcement(26404, title="Scheduled", message="hi",
                                 delayed_post_at="2026-11-06T20:00:00Z")
        # Simulate a held scheduled announcement (posted_at == created_at + delayed).
        fake.announcements["ambiguous"] = {
            "id": "ambiguous", "course_id": 26404, "title": "Ambiguous",
            "message": "hi", "published": True,
            "delayed_post_at": "2026-11-06T20:00:00Z", "posted_at": "2026-11-01T00:00:00Z",
        }
        obs = co.observe_canvas(fake, {"math": 26404})
        by_title = {a["title"]: a for a in obs["courses"]["math"]["announcements"]}
        self.assertEqual(by_title["Posted now"]["visibility"], co.POSTED)
        self.assertEqual(by_title["Scheduled"]["visibility"], co.SCHEDULED)
        # delayed + posted is ambiguous -> UNKNOWN (never guessed).
        self.assertEqual(by_title["Ambiguous"]["visibility"], co.UNKNOWN)

    def test_read_error_marks_unknown_not_fabricated(self) -> None:
        class FailingClient:
            def list_pages(self, course_id):
                raise RuntimeError("boom")

            def list_assignments(self, course_id):
                raise RuntimeError("boom")

            def list_announcements(self, course_id):
                raise RuntimeError("boom")

            def list_assignment_groups(self, course_id):
                raise RuntimeError("boom")

        obs = co.observe_canvas(FailingClient(), {"math": 26404})
        course = obs["courses"]["math"]
        self.assertIsNotNone(course["read_error"])
        self.assertEqual(course["assignments"], [])


if __name__ == "__main__":
    unittest.main()
