import unittest

from core.composio_backend import ComposioBackend


class FakeSession:
    def execute(self, tool_slug, *, arguments=None, account=None):
        return {
            "status": "completed",
            "data": {"result": "ok"},
        }


class TestComposioBackend(unittest.TestCase):
    def test_available_when_session_exists(self):
        backend = ComposioBackend(session=FakeSession())

        self.assertTrue(backend.available())

    def test_can_execute_composio_step(self):
        backend = ComposioBackend(session=FakeSession())

        self.assertTrue(
            backend.can_execute(
                {
                    "skill": "composio",
                    "tool_slug": "GITHUB_CREATE_ISSUE",
                }
            )
        )

    def test_cannot_execute_without_tool_slug(self):
        backend = ComposioBackend(session=FakeSession())

        self.assertFalse(
            backend.can_execute(
                {
                    "skill": "composio",
                }
            )
        )

    def test_execute_passes_tool_arguments_and_account(self):
        calls = []

        class TrackingSession:
            def execute(self, tool_slug, *, arguments=None, account=None):
                calls.append((tool_slug, arguments, account))
                return {
                    "status": "completed",
                    "data": {"result": "created"},
                }

        backend = ComposioBackend(session=TrackingSession())

        result = backend.execute(
            {
                "skill": "composio",
                "tool_slug": "GITHUB_CREATE_ISSUE",
                "arguments": {"title": "Test issue"},
                "account": "github_account",
            },
            "task_002",
        )

        self.assertEqual(
            calls,
            [
                (
                    "GITHUB_CREATE_ISSUE",
                    {"title": "Test issue"},
                    "github_account",
                )
            ],
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["task_id"], "task_002")


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
