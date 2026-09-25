import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.models import Plan, Task
from core.task_state_store import TaskStateStore


class TestTaskStateStore(unittest.TestCase):
    def test_save_and_load_task(self):
        with TemporaryDirectory() as tmp:
            store = TaskStateStore(Path(tmp))
            task = Task(
                task_id="task_test",
                request_id="req_test",
                status="running",
                current_step=2,
                plan=Plan(
                    request_id="req_test",
                    skills=["test-skill"],
                    steps=[
                        {
                            "step": 1,
                            "skill": "test-skill",
                            "status": "completed",
                            "result": {"status": "completed", "text": "Готово"},
                        }
                    ],
                ),
                artifacts=["result.txt"],
                errors=[],
            )

            store.save(task)

            path = Path(tmp) / "task_test.json"
            self.assertTrue(path.exists())

            restored = store.load("task_test")

            self.assertIsNotNone(restored)
            self.assertEqual(restored.task_id, task.task_id)
            self.assertEqual(restored.request_id, task.request_id)
            self.assertEqual(restored.status, "running")
            self.assertEqual(restored.current_step, 2)
            self.assertIsNotNone(restored.plan)
            self.assertEqual(restored.plan.skills, ["test-skill"])
            self.assertEqual(restored.plan.steps[0]["status"], "completed")
            self.assertEqual(restored.artifacts, ["result.txt"])

    def test_load_restores_persisted_state_after_in_memory_changes(self):
        with TemporaryDirectory() as tmp:
            store = TaskStateStore(tmp)
            task = Task(
                task_id="task_restore",
                request_id="req_restore",
                status="running",
                current_step=1,
                plan=Plan(
                    request_id="req_restore",
                    skills=["test-skill"],
                    steps=[
                        {
                            "step": 1,
                            "skill": "test-skill",
                            "status": "completed",
                            "result": {"status": "completed", "text": "Первый результат"},
                        },
                        {
                            "step": 2,
                            "skill": "test-skill-2",
                            "status": "pending",
                        },
                    ],
                ),
            )

            store.save(task)

            task.status = "failed"
            task.current_step = 2
            task.plan.steps[0]["status"] = "failed"

            restored = store.load("task_restore")

            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, "running")
            self.assertEqual(restored.current_step, 1)
            self.assertEqual(restored.plan.steps[0]["status"], "completed")
            self.assertEqual(
                restored.plan.steps[0]["result"]["text"],
                "Первый результат",
            )

    def test_load_missing_task_returns_none(self):
        with TemporaryDirectory() as tmp:
            store = TaskStateStore(tmp)

            self.assertIsNone(store.load("missing-task"))


if __name__ == "__main__":
    unittest.main()
