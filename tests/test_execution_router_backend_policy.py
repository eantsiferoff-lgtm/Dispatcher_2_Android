import unittest

from core.execution_router import ExecutionRouter
from core.openai_backend import OpenAIBackend
from core.composio_backend import ComposioBackend


class TestExecutionRouterBackendPolicy(unittest.TestCase):
    def test_specialized_composio_backend_beats_general_openai(self):
        router = ExecutionRouter()

        openai = OpenAIBackend(agent_runner=lambda text: "ai result")
        composio = ComposioBackend(
            session=object()
        )

        router.register("openai", openai)
        router.register("composio", composio)

        step = {
            "skill": "external-action",
            "tool_slug": "GMAIL_SEND_EMAIL",
        }

        self.assertEqual(router.route(step), "composio")


if __name__ == "__main__":
    unittest.main()
