import unittest
from pathlib import Path

from core.models import Request, Plan, Task, Result
from core.runtime import Runtime
from core.skill_executor import SkillExecutor


class TestRuntime(unittest.TestCase):
    def test_uses_default_config_when_file_is_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root)
            self.assertEqual(runtime.config.max_parallel_skills, 4)
            self.assertTrue(runtime.config.allow_multi_skill)

    def test_loads_dispatcher_config(self):
        runtime = Runtime(".")
        self.assertEqual(runtime.config.max_parallel_skills, 4)
        self.assertTrue(runtime.config.allow_multi_skill)
        self.assertEqual(runtime.config.registry_path, "registry.yaml")
        self.assertEqual(runtime.config.routing_path, "routing.yaml")

    def test_registers_openai_backend_when_factory_provided(self):
        from core.openai_backend import OpenAIBackend
        runtime = Runtime(".", openai_runner=lambda text: "ok")
        backend = runtime.execution_router.select("openai")
        self.assertIsInstance(backend, OpenAIBackend)
        self.assertEqual(backend.priority, 80)

    def test_multi_skill_plan_preserves_skill_order_and_dependencies(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare(
            "Проанализируй российский фондовый рынок по файлам проекта"
        )

        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertIn("file-project-analysis", plan.skills)
        self.assertEqual(len(plan.steps), 2)

        self.assertEqual(plan.steps[0]["step"], 1)
        self.assertEqual(plan.steps[1]["step"], 2)
        self.assertEqual(plan.steps[0]["status"], "pending")
        self.assertEqual(plan.steps[1]["status"], "pending")

        self.assertIn("depends_on", plan.steps[0])
        self.assertIn("depends_on", plan.steps[1])
        self.assertIn("execution_mode", plan.steps[0])
        self.assertIn("execution_mode", plan.steps[1])


    def test_prepare_creates_request_plan_and_task(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare("Проанализируй российский фондовый рынок")

        self.assertIsInstance(request, Request)
        self.assertIsInstance(plan, Plan)
        self.assertIsInstance(task, Task)

        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertEqual(task.request_id, request.request_id)
        self.assertIs(task.plan, plan)
        self.assertEqual(task.status, "pending")


    def test_prepare_persists_task_state(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)

            request, plan, task = runtime.prepare(
                "Проанализируй российский фондовый рынок"
            )

            path = Path(root) / "tasks" / f"{task.task_id}.json"
            self.assertTrue(path.exists())

    def test_restore_task_loads_persisted_task(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            runtime = Runtime(root, data_root=root)

            request, plan, task = runtime.prepare(
                "Проанализируй российский фондовый рынок"
            )

            restored = runtime.restore_task(task.task_id)

            self.assertIsNotNone(restored)
            self.assertEqual(restored.task_id, task.task_id)
            self.assertEqual(restored.request_id, request.request_id)
            self.assertEqual(restored.status, "pending")
            self.assertIsNotNone(restored.plan)

    def test_completed_task_state_is_persisted(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            skill_executor = SkillExecutor()
            skill_executor.register(
                "russian-investment-analysis",
                lambda step, task_id: {"text": "ok"},
            )

            runtime = Runtime(
                root,
                data_root=root,
                skill_executor=skill_executor,
            )

            request, plan, task, result = runtime.run(
                "Проанализируй российский фондовый рынок"
            )

            restored = runtime.restore_task(task.task_id)

            self.assertIsNotNone(restored)
            self.assertEqual(result.status, "completed")
            self.assertEqual(restored.status, "completed")
            self.assertEqual(restored.current_step, task.current_step)

    def test_failed_task_state_is_persisted(self):
        import tempfile
        from core.execution_router import ExecutionRouter

        class FailingBackend:
            priority = 100

            def available(self):
                return True

            def execute(self, step, task_id):
                raise RuntimeError("persistent failure")

        with tempfile.TemporaryDirectory() as root:
            router = ExecutionRouter()
            router.register("failing", FailingBackend())

            runtime = Runtime(
                root,
                data_root=root,
                execution_router=router,
            )

            request, plan, task = runtime.prepare(
                "Проанализируй российский фондовый рынок"
            )

            task.plan.steps = [
                {
                    "step": 1,
                    "skill": "test-skill",
                    "status": "pending",
                    "execution_mode": "ordered",
                    "depends_on": [],
                    "backend": "failing",
                }
            ]

            result = runtime.executor.execute(task)
            runtime.task_state_store.save(task)

            restored = runtime.restore_task(task.task_id)

            self.assertEqual(result.status, "failed")
            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, "failed")
            self.assertIn("persistent failure", restored.errors)

    def test_run_executes_full_pipeline(self):
        skill_executor = SkillExecutor()
        skill_executor.register("russian-investment-analysis", lambda step, task_id: {"text": "ok"})
        runtime = Runtime(".", skill_executor=skill_executor)
        request, plan, task, result = runtime.run("Проанализируй российский фондовый рынок")
        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertIn("russian-investment-analysis", plan.skills)
        self.assertEqual(task.status, "completed")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.task_id, task.task_id)


    def test_run_exposes_step_results_for_aggregation(self):
        skill_executor = SkillExecutor()
        skill_executor.register(
            "russian-investment-analysis",
            lambda step, task_id: {"text": "analysis result"},
        )

        runtime = Runtime(".", skill_executor=skill_executor)
        request, plan, task, result = runtime.run(
            "Проанализируй российский фондовый рынок"
        )

        step_results = [
            step.get("result")
            for step in task.plan.steps
            if step.get("result") is not None
        ]

        self.assertEqual(len(step_results), 1)
        self.assertEqual(step_results[0]["text"], "analysis result")

        normalized = runtime.result_aggregator.normalize(
            "russian-investment-analysis",
            Result(
                task_id=task.task_id,
                status="completed",
                text=step_results[0]["text"],
            ),
        )

        aggregated = runtime.result_aggregator.aggregate([normalized])

        self.assertEqual(aggregated["status"], "completed")
        self.assertEqual(aggregated["data"], ["analysis result"])

    def test_run_returns_aggregated_step_results(self):
        from core.planner import PlannerDecision

        skill_executor = SkillExecutor()
        skill_executor.register(
            "skill-a",
            lambda step, task_id: {"status": "completed", "text": "A"},
        )
        skill_executor.register(
            "skill-b",
            lambda step, task_id: {"status": "completed", "text": "B"},
        )

        runtime = Runtime(".", skill_executor=skill_executor)
        runtime.planner = type(
            "StubPlanner",
            (),
            {
                "plan": lambda self, text: PlannerDecision(
                    skills=["skill-a", "skill-b"],
                    workflow_id=None,
                    confidence=1.0,
                )
            },
        )()

        request, plan, task, result = runtime.run("test multi-skill aggregation")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.text, "[\"A\", \"B\"]")
        self.assertEqual(
            [step["result"]["text"] for step in task.plan.steps],
            ["A", "B"],
        )
        self.assertEqual(result.text, '["A", "B"]')

    def test_run_aggregates_parallel_step_results(self):
        import tempfile

        from core.planner import PlannerDecision

        with tempfile.TemporaryDirectory() as root:
            skills = SkillExecutor()
            skills.register(
                "skill-a",
                lambda step, task_id: {"status": "completed", "text": "A"},
            )
            skills.register(
                "skill-b",
                lambda step, task_id: {"status": "completed", "text": "B"},
            )

            root_path = Path(root)
            (root_path / "dispatcher.yaml").write_text(
                """version: "2.0"
registry: registry.yaml
routing: routing.yaml
orchestration:
  allow_multi_skill: true
  max_parallel_skills: 4
workflows:
  parallel-test:
    steps:
      - skill: skill-a
        depends_on: []
        execution_mode: parallel
      - skill: skill-b
        depends_on: []
        execution_mode: parallel
""",
                encoding="utf-8",
            )

            runtime = Runtime(root_path, skill_executor=skills)
            runtime.planner = type(
                "StubPlanner",
                (),
                {
                    "plan": lambda self, text: PlannerDecision(
                        skills=["skill-a", "skill-b"],
                        workflow_id="parallel-test",
                        confidence=1.0,
                    )
                },
            )()

            request, plan, task, result = runtime.run("parallel aggregation")

            self.assertEqual(result.status, "completed")
            self.assertEqual(result.text, '["A", "B"]')
            self.assertEqual(
                [step["result"]["text"] for step in task.plan.steps],
                ["A", "B"],
            )
            self.assertEqual(
                [step["execution_mode"] for step in task.plan.steps],
                ["parallel", "parallel"],
            )

    def test_run_preserves_single_result_text(self):
        from core.planner import PlannerDecision

        skills = SkillExecutor()
        skills.register(
            "skill-a",
            lambda step, task_id: {"status": "completed", "text": "A"},
        )

        runtime = Runtime(".", skill_executor=skills)
        runtime.planner = type(
            "StubPlanner",
            (),
            {
                "plan": lambda self, text: PlannerDecision(
                    skills=["skill-a"],
                    workflow_id=None,
                    confidence=1.0,
                )
            },
        )()

        request, plan, task, result = runtime.run("single result contract")

        self.assertEqual(result.status, "completed")
        self.assertEqual(result.text, "A")

    def test_run_integrates_verification(self):
        from core.planner import PlannerDecision

        skills = SkillExecutor()
        skills.register(
            "skill-a",
            lambda step, task_id: {"status": "completed", "text": "A"},
        )

        runtime = Runtime(".", skill_executor=skills)
        runtime.planner = type(
            "StubPlanner",
            (),
            {
                "plan": lambda self, text: PlannerDecision(
                    skills=["skill-a"],
                    workflow_id=None,
                    confidence=1.0,
                )
            },
        )()

        calls = []

        class StubVerification:
            def verify(self, result):
                calls.append(result)
                return {"status": "verified", "checks": []}

        runtime.verification = StubVerification()

        runtime.run("verification integration")

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].text, "A")

    def test_run_verifies_final_result(self):
        skill_executor = SkillExecutor()
        skill_executor.register(
            "russian-investment-analysis",
            lambda step, task_id: {"text": "verified result"},
        )

        runtime = Runtime(".", skill_executor=skill_executor)
        request, plan, task, result = runtime.run(
            "Проанализируй российский фондовый рынок"
        )

        verification = runtime.verification.verify(result)

        self.assertEqual(verification["status"], "verified")
        self.assertEqual(verification["checks"], [])

    def test_run_uses_execution_router_backend(self):
        from core.execution_router import ExecutionRouter

        class Backend:
            priority = 100

            def available(self):
                return True

            def execute(self, step, task_id):
                return {"status": "completed", "task_id": task_id}

        router = ExecutionRouter()
        router.register("test", Backend())

        runtime = Runtime(".", execution_router=router)

        request, plan, task = runtime.prepare(
            "Проанализируй российский фондовый рынок"
        )
        plan.steps[0]["backend"] = "test"

        result = runtime.executor.execute(task)

        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.task_id, task.task_id)
        self.assertEqual(task.status, "completed")


    def test_run_auto_uses_local_backend(self):
        from core.execution_router import ExecutionRouter
        from core.local_backend import LocalBackend
        from core.skill_executor import SkillExecutor

        skills = SkillExecutor()
        calls = []

        def handler(step, task_id):
            calls.append((step["skill"], task_id))
            return {"text": "ok"}

        skills.register("russian-investment-analysis", handler)
        local = LocalBackend(skills)
        router = ExecutionRouter()
        router.register("local", local)

        runtime = Runtime(".", execution_router=router)
        request, plan, task = runtime.prepare("Проанализируй российский фондовый рынок")
        result = runtime.executor.execute(task)

        self.assertEqual(result.status, "completed")
        self.assertEqual(task.status, "completed")
        self.assertEqual(calls[0][0], "russian-investment-analysis")




    def test_auto_refresh_lifecycle_can_be_enabled_or_disabled(self):
        runtime_on = Runtime(".", auto_refresh_lifecycle=True)
        runtime_off = Runtime(".", auto_refresh_lifecycle=False)
        self.assertTrue(runtime_on.auto_refresh_lifecycle)
        self.assertFalse(runtime_off.auto_refresh_lifecycle)

    def test_prepare_preserves_attachments_and_project(self):
        runtime = Runtime(".")
        request, plan, task = runtime.prepare(
            "Проанализируй рынок по файлам проекта",
            attachments=["/tmp/report.pdf", "/tmp/data.xlsx"],
            project_id="project_001",
        )

        self.assertEqual(
            request.attachments,
            ["/tmp/report.pdf", "/tmp/data.xlsx"],
        )
        self.assertEqual(request.project_id, "project_001")
        self.assertEqual(task.project_id, "project_001")
        self.assertEqual(task.status, "pending")


    def test_prepare_uses_workflow_from_dispatcher_config(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)

            (root_path / "dispatcher.yaml").write_text(
                """version: "2.0"
registry: registry.yaml
routing: routing.yaml
orchestration:
  allow_multi_skill: true
  max_parallel_skills: 4
workflows:
  market-report:
    steps:
      - skill: russian-investment-analysis
        depends_on: []
        execution_mode: parallel
""",
                encoding="utf-8",
            )

            runtime = Runtime(root_path)

            self.assertIn("market-report", runtime.config.workflows)

            from core.planner import PlannerDecision
            runtime.planner = type(
                "StubPlanner",
                (),
                {
                    "plan": lambda self, text: PlannerDecision(
                        skills=["russian-investment-analysis"],
                        workflow_id="market-report",
                        confidence=1.0,
                    )
                },
            )()

            request, plan, task = runtime.prepare(
                "Проанализируй российский фондовый рынок"
            )

            self.assertIn("russian-investment-analysis", plan.skills)
            self.assertEqual(plan.steps[0]["depends_on"], [])
            self.assertEqual(plan.steps[0]["execution_mode"], "parallel")


    def test_prepare_passes_selected_workflow_to_plan_builder(self):
        import tempfile

        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)

            (root_path / "dispatcher.yaml").write_text(
                """version: "2.0"
registry: registry.yaml
routing: routing.yaml
orchestration:
  allow_multi_skill: true
  max_parallel_skills: 4
workflows:
  market-report:
    steps:
      - skill: russian-investment-analysis
        depends_on: []
        execution_mode: parallel
""",
                encoding="utf-8",
            )

            runtime = Runtime(root_path)

            from core.planner import PlannerDecision

            runtime.planner = type(
                "StubPlanner",
                (),
                {
                    "plan": lambda self, text: PlannerDecision(
                        skills=["russian-investment-analysis"],
                        workflow_id="market-report",
                        confidence=1.0,
                    )
                },
            )()

            captured = {}

            class StubPlanBuilder:
                def build(self, request_id, decision, workflow=None):
                    captured["workflow"] = workflow
                    return PlanBuilder().build(
                        request_id,
                        decision,
                        workflow=workflow,
                    )

            from core.plan_builder import PlanBuilder
            runtime.plan_builder = StubPlanBuilder()

            runtime.prepare("Проанализируй российский фондовый рынок")

            self.assertEqual(
                captured["workflow"]["russian-investment-analysis"]["execution_mode"],
                "parallel",
            )


    def test_runtime_executes_dynamically_added_skill(self):
        import tempfile

        from core.skill_registry import SkillRegistry

        with tempfile.TemporaryDirectory() as root:
            skill_dir = Path(root) / "skills" / "dynamic-test-skill"
            skill_dir.mkdir(parents=True)

            (skill_dir / "SKILL.md").write_text(
                """---
name: dynamic-test-skill
description: Perform dynamic document verification.
metadata:
  version: "1.0"
  capabilities:
    - document-verification
  triggers:
    - проверь документ
  execution_mode: ordered
  backend: local
---
# Dynamic Test Skill

Created dynamically for the extensibility test.
""",
                encoding="utf-8",
            )

            registry = SkillRegistry(root)
            skill = registry.get("dynamic-test-skill")
            self.assertIsNotNone(skill)

            skills = SkillExecutor()
            calls = []

            def handler(step, task_id):
                calls.append((step["skill"], task_id))
                return {"text": "dynamic-skill-executed"}

            skills.register("dynamic-test-skill", handler)

            from core.local_backend import LocalBackend
            from core.execution_router import ExecutionRouter

            local = LocalBackend(skills)
            router = ExecutionRouter()
            router.register("local", local)

            runtime = Runtime(
                root,
                execution_router=router,
                skill_executor=skills,
            )

            runtime.planner = type(
                "StubPlanner",
                (),
                {
                    "plan": lambda self, text: __import__(
                        "core.planner",
                        fromlist=["PlannerDecision"],
                    ).PlannerDecision(
                        skills=["dynamic-test-skill"],
                        confidence=1.0,
                    )
                },
            )()

            request, plan, task = runtime.prepare("Проверь документ")

            self.assertEqual(
                plan.steps[0]["skill"],
                "dynamic-test-skill",
            )
            self.assertEqual(
                plan.steps[0]["backend"],
                "local",
            )

            result = runtime.executor.execute(task)

            self.assertEqual(result.status, "completed")
            self.assertEqual(task.status, "completed")
            self.assertEqual(
                result.text,
                "dynamic-skill-executed",
            )
            self.assertEqual(len(calls), 1)
            self.assertEqual(
                calls[0][0],
                "dynamic-test-skill",
            )

    def test_run_requires_confirmation_before_consequential_action(self):
        runtime = Runtime(".")
        calls = []

        class Backend:
            priority = 100

            def available(self):
                return True

            def execute(self, step, task_id):
                calls.append(step)
                return {"status": "completed", "task_id": task_id}

        runtime.execution_router.register("test", Backend())

        request, plan, task = runtime.prepare("Проанализируй российский фондовый рынок")
        plan.steps[0]["backend"] = "test"
        plan.steps[0]["action"] = "send"

        result = runtime.executor.execute(task)

        self.assertEqual(result.status, "confirmation_required")
        self.assertEqual(calls, [])
        self.assertTrue(any("CONFIRM" in warning for warning in result.warnings))


    def test_run_propagates_backend_error_to_failed_result_and_trace(self):
        from core.execution_router import ExecutionRouter

        class FailingBackend:
            priority = 100

            def available(self):
                return True

            def execute(self, step, task_id):
                raise RuntimeError("runtime backend boom")

        router = ExecutionRouter()
        router.register("failing", FailingBackend())

        runtime = Runtime(".", execution_router=router)

        request, plan, task = runtime.prepare(
            "Проанализируй российский фондовый рынок"
        )
        plan.steps[0]["backend"] = "failing"

        result = runtime.executor.execute(task)

        self.assertEqual(request.text, "Проанализируй российский фондовый рынок")
        self.assertEqual(result.status, "failed")
        self.assertEqual(task.status, "failed")
        self.assertEqual(result.task_id, task.task_id)

        events = runtime.execution_trace.events()

        self.assertTrue(any(
            event["event_type"] == "failed"
            and event["status"] == "failed"
            and event["backend"] == "failing"
            and event["error"] == "runtime backend boom"
            for event in events
        ))

if __name__ == "__main__":
    unittest.main()
