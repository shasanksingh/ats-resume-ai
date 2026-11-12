import unittest
import json
from unittest.mock import Mock, patch

import requests

from app.services.llm import nvidia_mistral_service as service


class NvidiaServiceTests(unittest.TestCase):
    def setUp(self):
        service._cache.clear()
        self.key_patch = patch.object(service, "NVIDIA_API_KEY", "test-key")
        self.key_patch.start()
        self.addCleanup(self.key_patch.stop)
        self.addCleanup(service._cache.clear)
        self.fallback_patch = patch.object(service, "NVIDIA_FALLBACK_MODEL", "")
        self.fallback_patch.start()
        self.addCleanup(self.fallback_patch.stop)

    def test_cache_preserves_selection_identity_without_expanding_remote_payload(self):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": '{"summary": null, "bullets": [{"improved":"A concise rewrite"}]}'}}]
        }
        first = {"original": "a" * 1600 + " first", "improved": "b" * 1700, "reason": "First"}
        second = {**first, "original": "a" * 1600 + " second"}
        with patch.object(service._session, "post", return_value=response) as post:
            result = service.refine_selected_changes("Shorten", "Engineer", None, [first])
            cached = service.refine_selected_changes("Shorten", "Engineer", None, [first])
            distinct = service.refine_selected_changes("Shorten", "Engineer", None, [second])
        self.assertEqual(post.call_count, 2)
        self.assertFalse(result["cached"])
        self.assertTrue(cached["cached"])
        self.assertEqual(distinct["bullets"][0]["original"], second["original"])
        prompt = post.call_args.kwargs["json"]["messages"][1]["content"]
        self.assertNotIn(second["original"], prompt)
        self.assertNotIn(first["improved"], prompt)

    def test_timeout_returns_actionable_error(self):
        with patch.object(service._session, "post", side_effect=requests.Timeout):
            with self.assertRaisesRegex(service.NvidiaServiceError, "timed out"):
                service.refine_selected_changes("Shorten", "Engineer", "Built APIs.", [])

    def test_timeout_uses_fast_nvidia_fallback_and_reports_actual_model(self):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"summary":"Built APIs.","bullets":[]}'}}]}
        with patch.object(service, "NVIDIA_FALLBACK_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"), patch.object(
            service._session, "post", side_effect=[requests.Timeout, response]
        ) as post:
            result = service.refine_selected_changes("Shorten", "Engineer", "Built APIs.", [])
        self.assertTrue(result["provider_fallback"])
        self.assertEqual(result["provider"], "nvidia/nemotron-3.5-lightning-30b-a3b")
        self.assertLessEqual(post.call_args_list[0].kwargs["timeout"], 45)
        self.assertFalse(post.call_args.kwargs["json"]["chat_template_kwargs"]["enable_thinking"])
        self.assertNotIn("reasoning_effort", post.call_args.kwargs["json"])

    def test_valid_bullets_survive_null_summary(self):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": '{"summary":null,"bullets":[{"improved":"Developed Python APIs."}]}'}}]}
        with patch.object(service._session, "post", return_value=response):
            result = service.refine_selected_changes("Improve", "Python", "Python engineer.", [{"original":"Built Python APIs.","improved":"Built Python APIs."}])
        self.assertEqual(result["summary"], "Python engineer.")
        self.assertEqual(result["bullets"][0]["improved"], "Developed Python APIs.")

    def test_one_failed_batch_does_not_discard_successful_edits(self):
        bullets = [{"original": f"Built Python APIs for {index} teams.", "improved": f"Built Python APIs for {index} teams."} for index in range(4)]
        def complete(payload, timeout):
            data = json.loads(payload["messages"][1]["content"].split("INPUT:\n")[1])
            if "0 teams" in data["bullets"][0]["original"]:
                raise service.NvidiaServiceError("Test timeout")
            return {"summary": None, "bullets": [{"improved": item["original"].replace("Built", "Developed")} for item in data["bullets"]]}
        with patch.object(service, "request_completion", side_effect=complete):
            result = service.refine_selected_changes("Improve", "Python", None, bullets)
        self.assertEqual(len(result["bullets"]), 4)
        self.assertTrue(result["warnings"])
        self.assertEqual(result["bullets"][0]["improved"], bullets[0]["original"])
        self.assertTrue(result["bullets"][2]["improved"].startswith("Developed"))

    def test_technical_qualifiers_and_acronyms_cannot_be_dropped(self):
        original = "Built domain-specific AI services with multi-agent workflows."
        self.assertFalse(service.preserves_evidence(original, "Built AI services with workflows."))
        self.assertFalse(service.preserves_evidence(original, "Built domain-specific services with multi-agent workflows."))

    def test_punctuation_only_changes_are_not_rewrites(self):
        original = "Built Python APIs."
        result = service.normalize_refinement({"bullets": [{"improved":"Built Python APIs!", "reason":"Improved clarity"}]}, None, [{"original":original,"improved":original}])
        self.assertEqual(result["bullets"][0]["improved"], original)
        self.assertIn("no distinct", result["bullets"][0]["reason"])

    def test_batched_rewrites_keep_all_selections_in_order(self):
        bullets = [{"original": f"Built Python services for {index} teams.", "improved": f"Built Python services for {index} teams."} for index in range(1, 9)]
        def complete(*args, **kwargs):
            data = json.loads(kwargs["json"]["messages"][1]["content"].split("INPUT:\n")[1])
            self.assertLessEqual(len(data["bullets"]), 2)
            response = Mock()
            response.json.return_value = {"choices": [{"message": {"content": json.dumps({
                "summary": data["summary"], "bullets": [{"improved": item["original"].replace("Built", "Developed")} for item in data["bullets"]]
            })}}]}
            return response
        with patch.object(service._session, "post", side_effect=complete) as post:
            result = service.refine_selected_changes("Improve", "Python", "Built Python services.", bullets)
        self.assertEqual(post.call_count, 4)
        self.assertEqual([b["original"] for b in result["bullets"]], [b["original"] for b in bullets])
        self.assertTrue(all(b["improved"].startswith("Developed") for b in result["bullets"]))

    def test_reasoning_budget_exhaustion_is_not_reported_as_success(self):
        response = Mock()
        response.json.return_value = {"choices": [{"finish_reason": "length", "message": {"content": None}}]}
        with patch.object(service._session, "post", return_value=response) as post:
            with self.assertRaisesRegex(service.NvidiaServiceError, "response limit"):
                service.refine_selected_changes("Shorten", "Engineer", "Built APIs.", [])
        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "low")

    def test_partial_and_empty_completions_are_not_success(self):
        for payload in ({"choices": []}, {"choices": [{"message": {"content": '{"summary":null,"bullets":[]}'}}]}):
            response = Mock()
            response.json.return_value = payload
            with patch.object(service._session, "post", return_value=response):
                with self.assertRaises(service.NvidiaServiceError):
                    service.refine_selected_changes("Shorten", "Engineer", None, [{"original":"Built APIs.", "improved":"Built APIs."}])

    def test_provider_failure_does_not_expose_credentials(self):
        response = Mock(status_code=401)
        error = requests.HTTPError("sensitive upstream details", response=response)
        with patch.object(service._session, "post", side_effect=error):
            with self.assertRaises(service.NvidiaServiceError) as caught:
                service.refine_selected_changes("Shorten", "Engineer", "Built APIs.", [])
        self.assertEqual(str(caught.exception), "NVIDIA refinement request failed (401).")

    def test_refinement_cannot_drop_metrics_or_add_unsupported_tools(self):
        original = "Developed Python APIs used by 120 teams."
        for rewrite in ("Developed Python APIs.", "Developed Python and AWS APIs used by 120 teams.", "Developed Python APIs used by 150 teams."):
            result = service.normalize_refinement({"bullets": [{"improved": rewrite}]}, None,
                [{"original": original, "improved": original}])
            self.assertEqual(result["bullets"][0]["improved"], original)
            self.assertIn("Original retained", result["bullets"][0]["reason"])

    def test_supported_rewording_keeps_evidence(self):
        self.assertTrue(service.preserves_evidence(
            "Responsible for developing Python APIs used by 120 teams.",
            "Developed Python APIs used by 120 teams.",
        ))
