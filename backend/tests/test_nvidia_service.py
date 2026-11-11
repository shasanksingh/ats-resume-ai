import unittest
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

    def test_cache_preserves_selection_identity_without_expanding_remote_payload(self):
        response = Mock()
        response.json.return_value = {
            "choices": [{"message": {"content": '{"summary": null, "bullets": []}'}}]
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

    def test_provider_failure_does_not_expose_credentials(self):
        response = Mock(status_code=401)
        error = requests.HTTPError("sensitive upstream details", response=response)
        with patch.object(service._session, "post", side_effect=error):
            with self.assertRaises(service.NvidiaServiceError) as caught:
                service.refine_selected_changes("Shorten", "Engineer", "Built APIs.", [])
        self.assertEqual(str(caught.exception), "NVIDIA refinement request failed (401).")
