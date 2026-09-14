import unittest

from core.composio_backend import ComposioBackend
from core.execution_router import ExecutionRouter


class FakeSession:
    def execute(self, tool_slug, *, arguments=None, account=None):
        return {
            "status": "completed",
            "data": {"result": "ok"},
        }


class TestExecutionRouterComposio(unittest.TestCase):
    def test_router_selects_composio_backend(self):
        router = ExecutionRouter()
        backend = ComposioBackend(session=FakeSession())

        router.register("composio", backend)

        selected = router.route(
            {
                "skill": "composio",
                "tool_slug": "GITHUB_CREATE_ISSUE",
            }
        )

        self.assertEqual(selected, "composio")


if __name__ == "__main__":
    unittest.main()
