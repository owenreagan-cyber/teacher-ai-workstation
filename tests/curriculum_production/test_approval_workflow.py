#!/usr/bin/env python3
"""Tests for teacher approval workflow."""
from __future__ import annotations

import sys
import unittest

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from scripts.curriculum_production.approval_workflow import ApprovalWorkflow, WorkflowState  # noqa: E402


class ApprovalWorkflowTests(unittest.TestCase):
    def test_draft_to_in_review(self) -> None:
        workflow = ApprovalWorkflow()
        record = workflow.transition(WorkflowState.IN_REVIEW, user="teacher")
        self.assertEqual(workflow.state, WorkflowState.IN_REVIEW)
        self.assertEqual(record.user, "teacher")

    def test_in_review_to_approved(self) -> None:
        workflow = ApprovalWorkflow(state=WorkflowState.IN_REVIEW)
        workflow.transition(WorkflowState.APPROVED, user="teacher", note="Ready")
        self.assertEqual(workflow.state, WorkflowState.APPROVED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
