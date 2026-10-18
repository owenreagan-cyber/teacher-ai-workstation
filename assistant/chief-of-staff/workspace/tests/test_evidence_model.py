from __future__ import annotations

import copy
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from evidence_model import (  # noqa: E402
    EVIDENCE_TYPES,
    expected_artifact_errors,
    make_shared_evidence_package,
    shared_evidence_errors,
    synthetic_math_expected_artifacts,
)


class SharedEvidenceModelTests(unittest.TestCase):
    def test_all_seven_evidence_types_share_one_contract(self) -> None:
        for index, evidence_type in enumerate(sorted(EVIDENCE_TYPES), start=1):
            package = make_shared_evidence_package(
                f"evidence-package:synthetic:{index}",
                evidence_type,
                "logical-resource:synthetic-subject",
                f"Synthetic {evidence_type} claim.",
                observations=[f"observation:synthetic:{index}"],
                confidence="medium",
            )
            self.assertEqual([], shared_evidence_errors(package))

    def test_evidence_does_not_create_authority_or_permission(self) -> None:
        package = make_shared_evidence_package(
            "evidence-package:synthetic:authority-isolation",
            "authority",
            "logical-resource:synthetic-subject",
            "Synthetic authority context exists.",
            authority_role="backup",
            authority_scope="backup_recovery",
            authority_basis="authority-assertion:synthetic",
            confidence="high",
        )
        self.assertEqual("none", package["authority_effect"])
        self.assertEqual("none", package["permission_effect"])
        self.assertEqual([], shared_evidence_errors(package))

    def test_confidence_and_review_state_are_independent(self) -> None:
        package = make_shared_evidence_package(
            "evidence-package:synthetic:review-separation",
            "classification",
            "logical-resource:synthetic-subject",
            "Synthetic classification claim.",
            observations=["classification-evidence:synthetic"],
            confidence="high",
            review_state="unreviewed",
        )
        self.assertEqual("high", package["confidence"])
        self.assertEqual("unreviewed", package["review_state"])
        self.assertEqual([], shared_evidence_errors(package))

    def test_unsupported_shared_evidence_type_is_rejected(self) -> None:
        package = make_shared_evidence_package(
            "evidence-package:synthetic:invalid",
            "action",
            "logical-resource:synthetic-subject",
            "Invalid claim.",
            observations=["observation:synthetic:invalid"],
        )
        self.assertTrue(shared_evidence_errors(package))

    def test_empty_evidence_and_unknown_basis_is_rejected(self) -> None:
        package = make_shared_evidence_package(
            "evidence-package:synthetic:empty",
            "availability",
            "logical-resource:synthetic-subject",
            "Unsupported empty claim.",
        )
        self.assertIn(
            "shared evidence package must cite evidence or an explicit basis",
            shared_evidence_errors(package),
        )

    def test_math_expected_artifact_relationships_are_nonexistence_claims(self) -> None:
        relationships = synthetic_math_expected_artifacts()
        self.assertEqual(3, len(relationships))
        self.assertEqual(
            {"presentation_pdf", "html_presentation", "teacher_notes"},
            {item["expected_artifact_type"] for item in relationships},
        )
        for relationship in relationships:
            self.assertEqual([], expected_artifact_errors(relationship))
            self.assertEqual("none", relationship["existence_claim"])
            self.assertEqual("unreviewed", relationship["review_state"])

    def test_expected_artifact_cannot_claim_current_existence(self) -> None:
        relationship = copy.deepcopy(synthetic_math_expected_artifacts()[0])
        relationship["existence_claim"] = "exists"
        self.assertTrue(expected_artifact_errors(relationship))


if __name__ == "__main__":
    unittest.main()
