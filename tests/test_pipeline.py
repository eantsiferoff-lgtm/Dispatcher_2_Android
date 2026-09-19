import unittest

from core.models import Request, Plan, Task, Result
from core.skill_registry import SkillRegistry
from core.planner import Planner
from core.plan_builder import PlanBuilder
from core.execution_trace import ExecutionTrace
from core.skill_executor import SkillExecutor
from core.executor import Executor


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


    def test_planner_to_executor_pipeline(self):
        registry = SkillRegistry(".")
        planner = Planner(registry)

        request = Request(
            request_id="REQ-INTEGRATION-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = planner.plan(request.text)

        self.assertIn("russian-investment-analysis", decision.skills)

        plan = PlanBuilder().build(
            request.request_id,
            decision,
        )

        self.assertIn("russian-investment-analysis", plan.skills)

        calls = []
        skill_executor = SkillExecutor()

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": "integration-ok"}

        skill_executor.register(
            "russian-investment-analysis",
            handler,
        )

        task = Task(
            task_id="TASK-INTEGRATION-001",
            request_id=request.request_id,
            plan=plan,
        )

        result = Executor(skill_executor).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(
            calls,
            [("russian-investment-analysis", "TASK-INTEGRATION-001")],
        )

    def test_planner_to_local_backend_pipeline(self):
        from core.local_backend import LocalBackend
        from core.execution_router import ExecutionRouter

        registry = SkillRegistry(".")
        planner = Planner(registry)

        request = Request(
            request_id="REQ-LOCAL-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = planner.plan(request.text)
        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "russian-investment-analysis": {
                    "depends_on": [],
                    "execution_mode": "ai",
                }
            },
        )

        calls = []

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": "local-backend-ok"}

        backend = LocalBackend()
        backend.register("russian-investment-analysis", handler)

        router = ExecutionRouter()
        router.register("local", backend)

        task = Task(
            task_id="TASK-LOCAL-001",
            request_id=request.request_id,
            plan=plan,
        )

        result = Executor(execution_router=router).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(
            calls,
            [("russian-investment-analysis", "TASK-LOCAL-001")],
        )

    def test_planner_to_openai_backend_pipeline(self):
        from core.openai_backend import OpenAIBackend
        from core.execution_router import ExecutionRouter

        registry = SkillRegistry(".")
        planner = Planner(registry)

        request = Request(
            request_id="REQ-OPENAI-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = planner.plan(request.text)
        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "russian-investment-analysis": {
                    "depends_on": [],
                    "execution_mode": "ai",
                }
            },
        )

        calls = []

        def runner(request_text):
            calls.append(request_text)
            return "openai-backend-ok"

        backend = OpenAIBackend(
            agent_runner=runner,
            request_provider=lambda task_id: request.text,
        )

        router = ExecutionRouter()
        router.register("openai", backend)

        task = Task(
            task_id="TASK-OPENAI-001",
            request_id=request.request_id,
            plan=plan,
        )

        trace = ExecutionTrace()

        result = Executor(
            execution_router=router,
            execution_trace=trace,
        ).execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(calls, [request.text])

        events = trace.__dict__["_events"]
        self.assertTrue(any(
            event["event_type"] == "backend_selected"
            and event["backend"] == "openai"
            for event in events
        ))

if __name__ == "__main__":
    unittest.main()
