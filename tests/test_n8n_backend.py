import unittest

from core.n8n_backend import N8NBackend


class FakeClient:
    def execute(self, workflow, payload=None):
        return {
            "status": "completed",
            "data": {"result": "ok"},
        }


class TestN8NBackend(unittest.TestCase):
    def test_available_when_client_exists(self):
        backend = N8NBackend(client=FakeClient())

        self.assertTrue(backend.available())

    def test_can_execute_n8n_step(self):
        backend = N8NBackend(client=FakeClient())

        self.assertTrue(
            backend.can_execute(
                {
                    "skill": "n8n",
                    "workflow": "market-analysis",
                }
            )
        )

    def test_cannot_execute_without_workflow(self):
        backend = N8NBackend(client=FakeClient())

        self.assertFalse(
            backend.can_execute(
                {
                    "skill": "n8n",
                }
            )
        )

    def test_execute_passes_workflow_and_payload(self):
        calls = []

        class TrackingClient:
            def execute(self, workflow, payload=None):
                calls.append((workflow, payload))
                return {
                    "status": "completed",
                    "data": {"result": "workflow done"},
                }

        backend = N8NBackend(client=TrackingClient())

        result = backend.execute(
            {
                "skill": "n8n",
                "workflow": "market-analysis",
                "payload": {"symbol": "SBER"},
            },
            "task_002",
        )

        self.assertEqual(
            calls,
            [
                (
                    "market-analysis",
                    {"symbol": "SBER"},
                )
            ],
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["task_id"], "task_002")



if __name__ == "__main__":
    unittest.main()