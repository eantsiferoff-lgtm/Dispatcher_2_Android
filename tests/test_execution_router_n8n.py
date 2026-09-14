import unittest

from core.execution_router import ExecutionRouter
from core.n8n_backend import N8NBackend


class FakeClient:
    def execute(self, workflow, payload=None):
        return {"status": "completed", "data": {"result": "ok"}}


class TestExecutionRouterN8N(unittest.TestCase):
    def test_router_selects_n8n_backend(self):
        router = ExecutionRouter()
        backend = N8NBackend(client=FakeClient())

        router.register("n8n", backend)

        selected = router.route(
            {
                "skill": "n8n",
                "workflow": "market-analysis",
            }
        )

        self.assertEqual(selected, "n8n")


if __name__ == "__main__":
    unittest.main()
