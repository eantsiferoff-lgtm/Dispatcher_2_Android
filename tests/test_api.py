import tempfile
from pathlib import Path
import unittest

from starlette.testclient import TestClient

from core.runtime import Runtime


class TestDispatcherAPI(unittest.TestCase):
    def test_post_request_creates_task(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)
            from core.api import create_app

            client = TestClient(create_app(runtime))

            response = client.post(
                "/request",
                json={
                    "text": "Проанализируй российский фондовый рынок",
                },
            )

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn("task_id", data)
            self.assertEqual(data["status"], "pending")

            task = runtime.restore_task(data["task_id"])
            self.assertIsNotNone(task)
            self.assertEqual(
                task.request_id,
                data["request_id"],
            )



    def test_get_workflows_returns_configured_workflows(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "dispatcher.yaml").write_text(
                """version: "2.0"
workflows:
  n8n-production:
    steps:
      - skill: n8n
        depends_on: []
        execution_mode: ordered
        backend: n8n
        workflow: n8n-production
""",
                encoding="utf-8",
            )

            runtime = Runtime(root, data_root=root)
            from core.api import create_app

            client = TestClient(create_app(runtime))

            response = client.get("/workflows")

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn("workflows", data)
            self.assertIsInstance(data["workflows"], list)

            workflow_ids = {
                item["workflow_id"]
                for item in data["workflows"]
            }

            self.assertIn("n8n-production", workflow_ids)


    def test_get_skills_returns_active_domain_skills(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)
            from core.api import create_app

            client = TestClient(create_app(runtime))

            response = client.get("/skills")

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn("skills", data)
            self.assertIsInstance(data["skills"], list)

            skill_ids = {item["skill_id"] for item in data["skills"]}
            self.assertNotIn("top-level-router", skill_ids)


    def test_get_task_trace_returns_execution_trace(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)
            from core.api import create_app

            client = TestClient(create_app(runtime))

            create_response = client.post(
                "/request",
                json={
                    "text": "Проанализируй российский фондовый рынок",
                },
            )

            task_id = create_response.json()["task_id"]

            response = client.get(f"/task/{task_id}/trace")

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertIn("events", data)
            self.assertGreaterEqual(len(data["events"]), 1)
            self.assertEqual(
                data["events"][0]["event_type"],
                "request",
            )
            self.assertEqual(
                data["events"][0]["task_id"],
                "",
            )



    def test_get_task_returns_persisted_task(self):
        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)
            from core.api import create_app

            client = TestClient(create_app(runtime))

            create_response = client.post(
                "/request",
                json={
                    "text": "Проанализируй российский фондовый рынок",
                },
            )

            task_id = create_response.json()["task_id"]

            response = client.get(f"/task/{task_id}")

            self.assertEqual(response.status_code, 200)

            data = response.json()
            self.assertEqual(data["task_id"], task_id)
            self.assertEqual(data["status"], "pending")
            self.assertIn("request_id", data)
            self.assertIn("workflow", data)
            self.assertIn("steps", data)
            self.assertIn("results", data)



if __name__ == "__main__":
    unittest.main()
