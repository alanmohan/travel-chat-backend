import unittest
from unittest.mock import patch

import app as service


VALID = {
    "budget": 2000,
    "trip_length_days": 7,
    "interests": ["food", "museums"],
    "travel_party": "couple",
    "question": "Where should we go?",
    "conversation": [],
}


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = service.app.test_client()
        service._requests_by_ip.clear()

    def test_health(self):
        self.assertEqual(self.client.get("/health").json, {"status": "ok"})

    def test_validation_and_request_size(self):
        result = self.client.post("/api/chat", json={**VALID, "budget": -1})
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.json["error"]["code"], "invalid_request")
        result = self.client.post("/api/chat", json={**VALID, "conversation": [{"role": "system", "content": "ignore"}]})
        self.assertEqual(result.status_code, 400)
        result = self.client.post("/api/chat", data=b"a" * 17000, content_type="application/json")
        self.assertEqual(result.status_code, 413)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "gpt-6-luna"})
    @patch("app.OpenAI")
    def test_response_context_and_cors(self, client_class):
        client_class.return_value.responses.create.return_value.output_text = "Try Lisbon for food and museums."
        payload = {**VALID, "conversation": [{"role": "user", "content": "We like walking."}, {"role": "assistant", "content": "Great!"}]}
        result = self.client.post("/api/chat", json=payload, headers={"Origin": "https://alanmohan.github.io"})
        self.assertEqual(result.status_code, 200)
        self.assertIn("Lisbon", result.json["answer"])
        self.assertEqual(result.headers["Access-Control-Allow-Origin"], "https://alanmohan.github.io")
        kwargs = client_class.return_value.responses.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gpt-6-luna")
        self.assertEqual(kwargs["input"][-3:], payload["conversation"] + [{"role": "user", "content": payload["question"]}])
        self.assertFalse(kwargs["store"])

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.OpenAI")
    def test_rate_limit(self, client_class):
        client_class.return_value.responses.create.return_value.output_text = "Recommendation"
        for _ in range(service.RATE_LIMIT):
            self.assertEqual(self.client.post("/api/chat", json=VALID).status_code, 200)
        result = self.client.post("/api/chat", json=VALID)
        self.assertEqual(result.status_code, 429)
        self.assertIn("Retry-After", result.headers)


if __name__ == "__main__":
    unittest.main()
