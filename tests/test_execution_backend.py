import unittest

from core.models import Plan, Task
from core.execution_backend import ExecutionBackend


class TestExecutionBackend(unittest.TestCase):
    def test_backend_contract(self):
        backend = ExecutionBackend()

        plan = Plan(request_id="req_001", skills=["russian-investment-analysis"], steps=[{"step": 1, "skill": "russian-investment-analysis", "status": "pending"}])
        task = Task(task_id="task_001", request_id="req_001", plan=plan)

        result = backend.execute(task)

        self.assertEqual(result.status, "planned")
        self.assertEqual(result.task_id, "task_001")


if __name__ == "__main__":
    unittest.main()
