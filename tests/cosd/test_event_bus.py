"""Event bus and SSE contract tests."""
from __future__ import annotations

import unittest

from cosd.event_bus import EventBus, get_event_bus


class EventBusTest(unittest.TestCase):
    def test_bounded_buffer(self):
        bus = EventBus()
        for i in range(300):
            bus.publish("task.test", task_id="a" * 32, detail={"i": i})
        self.assertLessEqual(len(bus.since(0)), 256)

    def test_subscriber_receives(self):
        bus = EventBus()
        seen = []
        bus.subscribe(lambda ev: seen.append(ev.type))
        bus.publish("task.completed", task_id="b" * 32, title="T")
        self.assertIn("task.completed", seen)

    def test_singleton(self):
        self.assertIs(get_event_bus(), get_event_bus())
