"""Session continuity through daemon ask path."""
from __future__ import annotations

import json
import unittest

from support import CosdStateTest, RunningServer, http_json

from cos.sessions import read_turns


class SessionContinuityTests(CosdStateTest):
    def setUp(self):
        super().setUp()
        self.srv = RunningServer(self.state)

    def tearDown(self):
        self.srv.stop()
        super().tearDown()

    def test_daemon_ask_appends_session(self):
        sid = "test-session"
        http_json(
            self.srv.port,
            "/v1/ask",
            method="POST",
            token=self.srv.token,
            body={"question": "what time is it", "session_id": sid},
        )
        turns = read_turns(self.state, sid)
        self.assertEqual(len(turns), 1)
        srv2 = RunningServer(self.state)
        try:
            http_json(
                srv2.port,
                "/v1/ask",
                method="POST",
                token=srv2.token,
                body={"question": "what time is it", "session_id": sid},
            )
        finally:
            srv2.stop()
        self.assertEqual(len(read_turns(self.state, sid)), 2)
