import unittest
from datetime import datetime
from unittest import mock

from scripts.weekly_planner_agent import activation, service
from scripts.weekly_planner_agent import publish as pub
from scripts.weekly_planner_agent import delivery, schedule_config

ET = activation.EASTERN


class ScheduledPublishTests(unittest.TestCase):

    def test_blocked_gate_never_constructs_live_client(self):
        with (
            mock.patch.object(service, "load_plan", return_value=None),
            mock.patch.object(
                pub, "build_publish_gate",
                return_value={"ready": False, "blockers": ["approval missing"]}
            ),
            mock.patch(
                "scripts.canvas_llm_deploy.client.LiveDeployClient"
            ) as factory,
            mock.patch.object(pub, "publish") as publisher,
        ):
            result = activation.publish_scheduled(2, 5)

        self.assertEqual(result["state"], "BLOCKED")
        self.assertEqual(result["canvas_writes"], 0)
        factory.assert_not_called()
        publisher.assert_not_called()

    def test_approved_gate_constructs_live_client_and_publishes(self):
        fake_client = object()
        report = {"verb_totals": {"GET": 4, "PUT": 5, "POST": 9}}

        with (
            mock.patch.object(service, "load_plan", return_value=None),
            mock.patch.object(
                pub, "build_publish_gate",
                return_value={"ready": True, "blockers": []}
            ),
            mock.patch(
                "scripts.canvas_llm_deploy.client.LiveDeployClient",
                return_value=fake_client,
            ) as factory,
            mock.patch.object(
                pub, "publish",
                return_value={
                    "published": True,
                    "review_state": "PUBLISHED_VERIFIED",
                    "report": report,
                },
            ) as publisher,
        ):
            result = activation.publish_scheduled(
                2, 5,
                now=datetime(2026, 11, 6, 16, 0, tzinfo=ET),
            )

        factory.assert_called_once_with()
        self.assertIs(publisher.call_args.kwargs["client"], fake_client)
        self.assertTrue(result["published"])
        self.assertEqual(result["state"], "PUBLISHED_VERIFIED")
        self.assertEqual(result["canvas_writes"], 14)

    def test_disabled_email_is_suppressed_without_delivery_attempt(self):
        with (
            mock.patch.object(service, "load_plan", return_value=object()),
            mock.patch.object(
                service, "friday_review",
                return_value={"state": "READY_FOR_REVIEW"},
            ),
            mock.patch.object(
                schedule_config, "delivery_config",
                return_value={"email_enabled": False},
            ),
            mock.patch.object(delivery, "make_record") as make_record,
            mock.patch.object(delivery, "deliver") as deliver,
        ):
            result = service.friday_notify(2, 5)

        self.assertFalse(result["sent"])
        self.assertEqual(result["status"], "EMAIL_DISABLED")
        self.assertEqual(result["canvas_writes"], 0)
        make_record.assert_not_called()
        deliver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
