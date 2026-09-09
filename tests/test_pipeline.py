import unittest

from core.models import Request, Plan, Task, Result


class TestPipeline(unittest.TestCase):
    def test_request_to_result(self):
        request = Request(
            request_id="REQ-000001",
            text="Проанализируй российский фондовый рынок",
        )

        plan = Plan(
            request_id=request.request_id,
            skills=["russian-investment-analysis"],
            steps=[
                {"step": 1, "action": "analyze"},
                {"step": 2, "action": "verify"},
            ],
        )

        task = Task(
            task_id="TASK-000001",
            request_id=request.request_id,
            plan=plan,
            status="running",
            current_step=1,
        )

        result = Result(
            task_id=task.task_id,
            status="completed",
            text="Анализ завершён",
        )

        self.assertEqual(plan.request_id, request.request_id)
        self.assertEqual(task.request_id, request.request_id)
        self.assertIs(task.plan, plan)
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(result.status, "completed")


if __name__ == "__main__":
    unittest.main()
