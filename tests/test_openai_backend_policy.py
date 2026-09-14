import unittest

from core.openai_backend import OpenAIBackend


class TestOpenAIBackendPolicy(unittest.TestCase):
    def setUp(self):
        self.backend = OpenAIBackend(agent_runner=lambda text: "ai result")

    def test_can_execute_explicit_openai_backend(self):
        step = {
            "skill": "analysis",
            "backend": "openai",
        }

        self.assertTrue(self.backend.can_execute(step))

    def test_can_execute_ai_execution_mode(self):
        step = {
            "skill": "analysis",
            "execution_mode": "ai",
        }

        self.assertTrue(self.backend.can_execute(step))

    def test_does_not_claim_composio_step(self):
        step = {
            "skill": "external-action",
            "tool_slug": "GMAIL_SEND_EMAIL",
        }

        self.assertFalse(self.backend.can_execute(step))

    def test_does_not_claim_n8n_step(self):
        step = {
            "skill": "workflow-action",
            "workflow": "customer-sync",
        }

        self.assertFalse(self.backend.can_execute(step))


if __name__ == "__main__":
    unittest.main()
