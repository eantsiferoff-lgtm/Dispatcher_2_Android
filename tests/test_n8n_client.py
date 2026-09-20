import unittest
from unittest.mock import patch

from core.n8n_client import N8NClient


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"result": "n8n-ok"}


class TestN8NClient(unittest.TestCase):
    @patch("core.n8n_client.requests.post")
    def test_execute_posts_json_to_webhook(self, post):
        post.return_value = FakeResponse()

        client = N8NClient("https://example.test/webhook")
        result = client.execute(
            "market-analysis",
            {"source": "dispatcher"},
        )

        post.assert_called_once_with(
            "https://example.test/webhook",
            json={"source": "dispatcher"},
            timeout=30.0,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["data"], {"result": "n8n-ok"})


if __name__ == "__main__":
    unittest.main()
