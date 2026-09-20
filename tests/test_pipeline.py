import unittest

from core.models import Request, Plan, Task, Result
from core.skill_registry import SkillRegistry
from core.planner import Planner
from core.planner import PlannerDecision

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

        request = Request(
            request_id="REQ-INTEGRATION-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = PlannerDecision(skills=["russian-investment-analysis"], confidence=1.0)

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


        request = Request(
            request_id="REQ-LOCAL-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = PlannerDecision(skills=["russian-investment-analysis"], confidence=1.0)
        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "russian-investment-analysis": {
                    "depends_on": [],
                    "backend": "local",
                    "execution_mode": "ordered",
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


        request = Request(
            request_id="REQ-OPENAI-001",
            text="Проанализируй российский фондовый рынок",
        )

        decision = PlannerDecision(skills=["russian-investment-analysis"], confidence=1.0)
        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "russian-investment-analysis": {
                    "depends_on": [],
                    "backend": "openai",
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

    def test_planner_to_n8n_backend_pipeline(self):
        from core.execution_router import ExecutionRouter
        from core.n8n_backend import N8NBackend

        request = Request(
            request_id="REQ-N8N-001",
            text="Запусти n8n workflow анализа рынка",
        )

        decision = PlannerDecision(
            skills=["n8n"],
            confidence=1.0,
        )

        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "n8n": {
                    "depends_on": [],
                    "backend": "n8n",
                    "execution_mode": "ordered",
                    "workflow": "market-analysis",
                },
            },
        )

        calls = []

        class TrackingClient:
            def execute(self, workflow, payload=None):
                calls.append((workflow, payload))
                return {
                    "status": "completed",
                    "data": {"result": "n8n-workflow-ok"},
                }

        backend = N8NBackend(client=TrackingClient())
        router = ExecutionRouter()
        router.register("n8n", backend)

        task = Task(
            task_id="TASK-N8N-001",
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
        self.assertEqual(
            calls,
            [("market-analysis", None)],
        )

        events = trace.__dict__["_events"]
        self.assertTrue(any(
            event["event_type"] == "backend_selected"
            and event["backend"] == "n8n"
            for event in events
        ))
        self.assertTrue(any(
            event["event_type"] == "completed"
            and event["backend"] == "n8n"
            and event["status"] == "completed"
            for event in events
        ))

    def test_planner_to_composio_github_pipeline(self):
        import os
        from dotenv import dotenv_values
        from composio import Composio
        from core.composio_backend import ComposioBackend
        from core.execution_router import ExecutionRouter

        env = dotenv_values(".env")

        client = Composio(api_key=env["COMPOSIO_API_KEY"])

        class SessionAdapter:
            def execute(self, tool_slug, *, arguments=None, account=None):
                return client.tools.execute(
                    tool_slug,
                    arguments=arguments or {},
                    user_id="user_001",
                    version="20260916_00",
                )


        request = Request(
            request_id="REQ-C-REAL",
            text="Получи информацию о текущем пользователе GitHub",
        )

        decision = PlannerDecision(skills=["github"], confidence=1.0)

        plan = PlanBuilder().build(
            request.request_id,
            decision,
            workflow={
                "github": {
                    "depends_on": [],
                    "backend": "composio",
                    "tool_slug": "GITHUB_GET_THE_AUTHENTICATED_USER",
                },
            },
        )

        backend = ComposioBackend(session=SessionAdapter())
        router = ExecutionRouter()
        router.register("composio", backend)

        task = Task(
            task_id="TASK-C-REAL",
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

        events = trace.__dict__["_events"]
        self.assertTrue(any(
            event["event_type"] == "backend_selected"
            and event["backend"] == "composio"
            for event in events
        ))
        self.assertTrue(any(
            event["event_type"] == "completed"
            and event["backend"] == "composio"
            and event["status"] == "completed"
            for event in events
        ))

    def test_runtime_to_real_n8n_production_pipeline(self):
        import os
        from pathlib import Path
        from dotenv import dotenv_values

        env = dotenv_values(".env")

        from core.planner import PlannerDecision
        from core.runtime import Runtime

        n8n_webhook_url = env.get("N8N_WEBHOOK_URL")
        if not n8n_webhook_url:
            self.skipTest("N8N_WEBHOOK_URL is not set")

        previous_n8n_url = os.environ.get("N8N_WEBHOOK_URL")
        os.environ["N8N_WEBHOOK_URL"] = n8n_webhook_url
        try:
            runtime = Runtime(Path("."))

            runtime.planner = type(
                "StubPlanner",
                (),
                {
                    "plan": lambda self, text: PlannerDecision(
                        skills=["n8n"],
                        confidence=1.0,
                        workflow_id="n8n-production",
                    )
                },
            )()

            request, plan, task, result = runtime.run(
                "Запусти опубликованный n8n workflow"
            )

            self.assertEqual(result.status, "completed")
            self.assertEqual(task.status, "completed")
            self.assertEqual(plan.steps[0]["backend"], "n8n")
            self.assertEqual(plan.steps[0]["workflow"], "n8n-production")
        finally:
            if previous_n8n_url is not None:
                os.environ["N8N_WEBHOOK_URL"] = previous_n8n_url
            else:
                os.environ.pop("N8N_WEBHOOK_URL", None)

if __name__ == "__main__":
    unittest.main()