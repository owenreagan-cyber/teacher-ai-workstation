from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ai_context_adapter import synthetic_local_model_boundary_bundle
from grounding_contract import (
    CONTRACT_METADATA,
    GROUNDING_VIOLATION_CODES,
    RESPONSE_V2_SCHEMA_PATH,
    V2_OUTPUT_RULES,
    build_ideal_response_v2,
    build_response_vocabulary,
    prompt_schema_consistency_errors,
    prompt_vocabulary,
    render_validated_explanation_v2,
    validate_grounding_response_v2,
)
from validate import load_json, validate_schema


ROOT = Path(__file__).resolve().parents[1]


class GroundingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle = synthetic_local_model_boundary_bundle()
        cls.context = cls.bundle["context"]
        cls.request = cls.bundle["request"]
        cls.ideal = build_ideal_response_v2(cls.context, cls.request)

    def validate(self, candidate, *, context=None):
        return validate_grounding_response_v2(
            candidate, self.request, context or self.context
        )

    @staticmethod
    def codes(result):
        return {item["code"] for item in result["violations"]}

    def test_exact_closed_reference_response_passes(self) -> None:
        result = self.validate(self.ideal)
        self.assertTrue(result["accepted"])
        self.assertEqual("none", result["failure_category"])
        validate_schema(self.ideal, load_json(RESPONSE_V2_SCHEMA_PATH))

    def test_v1_prose_contract_remains_separate(self) -> None:
        self.assertEqual(1, self.bundle["response"]["schema_version"])
        self.assertEqual(2, self.ideal["schema_version"])
        self.assertIn("claims", self.bundle["response"])
        self.assertNotIn("claims", self.ideal)

    def test_semantic_paraphrase_field_is_not_accepted(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["known"] = ["A reasonable paraphrase."]
        result = self.validate(candidate)
        self.assertFalse(result["accepted"])
        self.assertIn("UNKNOWN_RESPONSE_FIELD", self.codes(result))

    def test_invented_evidence_reference_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["evidence_refs"][0] = "evidence:999"
        result = self.validate(candidate)
        self.assertIn("EVIDENCE_CLAIM_UNSUPPORTED", self.codes(result))
        self.assertIn("EVIDENCE_CLAIM_MISSING", self.codes(result))

    def test_missing_uncertainty_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["uncertainty_refs"].pop()
        result = self.validate(candidate)
        self.assertIn("UNCERTAINTY_MISSING", self.codes(result))
        self.assertIn("UNCERTAINTY_COUNT_MISMATCH", self.codes(result))

    def test_authority_synonym_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["authority"] = "unverified"
        result = self.validate(candidate)
        self.assertEqual("authority_violation", result["failure_category"])
        self.assertIn("AUTHORITY_CHANGED", self.codes(result))

    def test_confidence_upgrade_is_rejected(self) -> None:
        context = copy.deepcopy(self.context)
        subject = context["entities"][0]["entity_id"]
        next(
            item for item in context["confidence"] if item["subject_ref"] == subject
        )["value"] = "medium"
        candidate = build_ideal_response_v2(context, self.request)
        candidate["confidence"] = "high"
        result = self.validate(candidate, context=context)
        self.assertIn("CONFIDENCE_CHANGED", self.codes(result))

    def test_relationship_inference_is_excluded(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["relationship_refs"] = ["relationship:001"]
        result = self.validate(candidate)
        self.assertEqual("capability_violation", result["failure_category"])
        self.assertIn("RELATIONSHIP_UNSUPPORTED", self.codes(result))

    def test_helpful_recommendation_is_rejected(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["recommendations"] = ["Review this application."]
        result = self.validate(candidate)
        self.assertIn("RECOMMENDATION_CONTENT_PRESENT", self.codes(result))

    def test_extra_prose_outside_json_is_malformed(self) -> None:
        encoded = json.dumps(self.ideal) + "\nHelpful note"
        with self.assertRaises(json.JSONDecodeError):
            json.loads(encoded)

    def test_unknown_and_duplicate_references_are_rejected(self) -> None:
        unknown = copy.deepcopy(self.ideal)
        unknown["known_refs"] = ["known:999"]
        self.assertIn("KNOWN_CLAIM_UNSUPPORTED", self.codes(self.validate(unknown)))
        duplicate = copy.deepcopy(self.ideal)
        duplicate["evidence_refs"].append(duplicate["evidence_refs"][0])
        self.assertIn("DUPLICATE_REFERENCE", self.codes(self.validate(duplicate)))

    def test_all_required_reference_cardinalities_are_exact(self) -> None:
        for field, code in (
            ("known_refs", "KNOWN_CLAIM_MISSING"),
            ("evidence_refs", "EVIDENCE_CLAIM_MISSING"),
            ("uncertainty_refs", "UNCERTAINTY_MISSING"),
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.ideal)
                candidate[field].pop()
                self.assertIn(code, self.codes(self.validate(candidate)))

    def test_exact_enums_are_preserved(self) -> None:
        for field, value, code in (
            ("authority", "canonical", "AUTHORITY_CHANGED"),
            ("confidence", "low", "CONFIDENCE_CHANGED"),
            ("review_state", "approved", "REVIEW_STATE_CHANGED"),
            ("action_authority", "granted", "INVALID_ENUM_VALUE"),
        ):
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.ideal)
                candidate[field] = value
                self.assertIn(code, self.codes(self.validate(candidate)))

    def test_every_diagnostic_is_safe_and_finite(self) -> None:
        candidate = copy.deepcopy(self.ideal)
        candidate["evidence_refs"] = ["evidence:999"]
        candidate["recommendations"] = ["private rejected prose /Users/example"]
        result = self.validate(candidate)
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("private rejected prose", encoded)
        self.assertNotIn("/Users/", encoded)
        self.assertFalse(result["raw_response_retained"])
        self.assertFalse(result["persisted"])
        self.assertTrue(self.codes(result) <= GROUNDING_VIOLATION_CODES)

    def test_renderer_uses_only_validated_context_references(self) -> None:
        first = render_validated_explanation_v2(self.ideal, self.request, self.context)
        second = render_validated_explanation_v2(self.ideal, self.request, self.context)
        self.assertEqual(first, second)
        self.assertIn(self.context["entities"][0]["summary"], first)
        self.assertNotIn("known:001", first)
        rejected = copy.deepcopy(self.ideal)
        rejected["known_refs"] = ["known:999"]
        with self.assertRaises(ValueError):
            render_validated_explanation_v2(rejected, self.request, self.context)

    def test_round_trip_context_request_response_validator_renderer(self) -> None:
        vocabulary = build_response_vocabulary(self.context, self.request)
        response = build_ideal_response_v2(self.context, self.request)
        validation = validate_grounding_response_v2(
            response, self.request, self.context
        )
        rendered = render_validated_explanation_v2(
            response, self.request, self.context
        )
        self.assertEqual("local-model-response.v2", vocabulary["contract_id"])
        self.assertTrue(validation["accepted"])
        self.assertTrue(rendered.startswith("Subject: Grade 4 Writing Launcher"))

    def test_prompt_schema_metadata_are_consistent(self) -> None:
        self.assertEqual([], prompt_schema_consistency_errors())
        joined = "\n".join(V2_OUTPUT_RULES)
        for field in CONTRACT_METADATA:
            if field != "contract_id":
                self.assertIn(f"{field}:", joined)

    def test_prompt_vocabulary_contains_no_rendering_maps(self) -> None:
        vocabulary = prompt_vocabulary(
            build_response_vocabulary(self.context, self.request)
        )
        self.assertFalse(any(key.startswith("_") for key in vocabulary))
        encoded = json.dumps(vocabulary, sort_keys=True)
        self.assertNotIn(self.context["entities"][0]["summary"], encoded)

    def test_contract_module_has_no_runtime_or_persistence_primitive(self) -> None:
        source = (ROOT / "grounding_contract.py").read_text(encoding="utf-8").lower()
        for forbidden in (
            "import socket", "import subprocess", "from urllib", "requests.",
            "/api/chat", "ollama serve", "write_text", "open(\"w", "open('w",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
